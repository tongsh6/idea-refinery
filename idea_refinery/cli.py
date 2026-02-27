from __future__ import annotations

import json
import os

import click
from dotenv import load_dotenv

from .config import GateConfig, REVIEWER_HATS, RunConfig
from .orchestrator import run_full_pipeline
from .providers import OpenAIProviderSpec, build_registry
from .store import SqliteStore


@click.group()
def main() -> None:
    _ = load_dotenv()


def _parse_openai_provider_entry(entry: str) -> OpenAIProviderSpec:
    parts = [p.strip() for p in entry.split(",")]
    if len(parts) != 4:
        raise click.BadParameter(
            "--openai-provider format must be: name,base_url,model,api_key_env"
        )
    name, base_url, model, api_key_env = parts
    api_key = os.getenv(api_key_env, "")
    if not api_key:
        raise click.BadParameter(f"Environment variable '{api_key_env}' is empty")
    return OpenAIProviderSpec(name=name, base_url=base_url, api_key=api_key, model=model)


def _parse_openai_provider_json(payload: str | None) -> list[OpenAIProviderSpec]:
    if not payload:
        return []
    try:
        raw_obj: object = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise click.BadParameter("OPENAI_COMPAT_PROVIDERS_JSON is invalid JSON") from exc
    if not isinstance(raw_obj, list):
        raise click.BadParameter("OPENAI_COMPAT_PROVIDERS_JSON must be a JSON array")
    raw_list: list[object] = list(raw_obj)

    specs: list[OpenAIProviderSpec] = []
    for item in raw_list:
        if not isinstance(item, dict):
            raise click.BadParameter("Each provider entry in JSON must be an object")
        item_map: dict[str, object] = {str(k): v for k, v in item.items()}
        name = str(item_map.get("name", "")).strip()
        base_url = str(item_map.get("base_url", "")).strip()
        model = str(item_map.get("model", "")).strip()
        api_key = str(item_map.get("api_key", "")).strip()
        api_key_env = str(item_map.get("api_key_env", "")).strip()
        if not api_key and api_key_env:
            api_key = os.getenv(api_key_env, "")
        if not (name and base_url and model and api_key):
            raise click.BadParameter(
                "Provider JSON entry requires name/base_url/model and api_key or api_key_env"
            )
        specs.append(OpenAIProviderSpec(name=name, base_url=base_url, api_key=api_key, model=model))
    return specs


def _parse_role_map_json(payload: str | None) -> dict[str, str]:
    if not payload:
        return {}
    try:
        raw_obj: object = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise click.BadParameter("ROLE_PROVIDER_MAP_JSON is invalid JSON") from exc
    if not isinstance(raw_obj, dict):
        raise click.BadParameter("ROLE_PROVIDER_MAP_JSON must be a JSON object")
    raw_map: dict[object, object] = dict(raw_obj)
    out: dict[str, str] = {}
    for k, v in raw_map.items():
        role = str(k).strip()
        provider = str(v).strip()
        if role and provider:
            out[role] = provider
    return out


def _parse_role_provider_pairs(items: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise click.BadParameter("--role-provider format must be: role=provider")
        role, provider = [p.strip() for p in item.split("=", 1)]
        if not role or not provider:
            raise click.BadParameter("--role-provider requires non-empty role and provider")
        out[role] = provider
    return out


@main.command()
@click.option("--idea", required=True, help="Idea text to refine")
@click.option("--out", "output_dir", default="./out", show_default=True)
@click.option("--budget", "budget_usd", default=1.0, show_default=True, type=float)
@click.option("--max-rounds", default=6, show_default=True, type=int)
@click.option("--reviewer-hats", default=None, help="Comma-separated reviewer hats")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--openai-base-url", default=None)
@click.option("--openai-model", default=None)
@click.option(
    "--openai-provider",
    "openai_providers",
    multiple=True,
    help="name,base_url,model,api_key_env",
)
@click.option(
    "--role-provider",
    "role_providers",
    multiple=True,
    help="role=provider",
)
@click.option("--ollama-model", default=None)
@click.option("--ollama", "use_ollama", is_flag=True, default=False)
def run(
    idea: str,
    output_dir: str,
    budget_usd: float,
    max_rounds: int,
    reviewer_hats: str | None,
    dry_run: bool,
    openai_base_url: str | None,
    openai_model: str | None,
    openai_providers: tuple[str, ...],
    role_providers: tuple[str, ...],
    ollama_model: str | None,
    use_ollama: bool,
) -> None:
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = openai_base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = openai_model or os.getenv("DEFAULT_MODEL") or "gpt-4o-mini"
    ollama_model_value = ollama_model or os.getenv("OLLAMA_MODEL") or "qwen3:30b"
    db_path = os.getenv("DB_PATH", "./refinery.db")
    openai_specs = _parse_openai_provider_json(os.getenv("OPENAI_COMPAT_PROVIDERS_JSON"))
    openai_specs.extend([_parse_openai_provider_entry(item) for item in openai_providers])
    role_map = _parse_role_map_json(os.getenv("ROLE_PROVIDER_MAP_JSON"))
    role_map.update(_parse_role_provider_pairs(role_providers))

    registry = build_registry(
        openai_api_key=openai_api_key,
        openai_base_url=base_url,
        openai_model=model,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=ollama_model_value,
        openai_compat_specs=openai_specs,
        include_ollama=use_ollama,
    )
    if role_map:
        registry.set_role_map(role_map)

    gate = GateConfig(budget_usd=budget_usd, max_rounds=max_rounds)
    hats = None
    if reviewer_hats:
        hats = [h.strip() for h in reviewer_hats.split(",") if h.strip()]

    config = RunConfig(
        idea=idea,
        gate=gate,
        output_dir=output_dir,
        dry_run=dry_run,
        reviewer_hats=hats or list(REVIEWER_HATS),
    )
    store = SqliteStore(db_path)

    outputs = run_full_pipeline(config=config, registry=registry, store=store)
    click.echo(f"PRD written to {outputs['PRD']}")
    click.echo(f"TECH_SPEC written to {outputs['TECH_SPEC']}")
    click.echo(f"EXEC_PLAN written to {outputs['EXEC_PLAN']}")


if __name__ == "__main__":
    main()
