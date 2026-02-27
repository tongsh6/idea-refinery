from idea_refinery.providers import OpenAIProviderSpec, build_registry


def test_build_registry_with_multiple_openai_compatible_providers() -> None:
    specs = [
        OpenAIProviderSpec(
            name="kimi",
            base_url="https://api.moonshot.cn/v1",
            api_key="k1",
            model="moonshot-v1-8k",
        ),
        OpenAIProviderSpec(
            name="glm",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            api_key="k2",
            model="glm-4.5",
        ),
    ]
    registry = build_registry(openai_compat_specs=specs)
    names = [p.name for p in registry.all()]
    assert names == ["kimi", "glm"]


def test_resolve_candidates_honors_role_provider_preference() -> None:
    specs = [
        OpenAIProviderSpec(
            name="kimi",
            base_url="https://api.moonshot.cn/v1",
            api_key="k1",
            model="moonshot-v1-8k",
        ),
        OpenAIProviderSpec(
            name="glm",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            api_key="k2",
            model="glm-4.5",
        ),
    ]
    registry = build_registry(openai_compat_specs=specs)
    registry.set_role_map({"author": "glm"})
    names = [p.name for p in registry.resolve_candidates("author")]
    assert names[0] == "glm"
    assert set(names) == {"kimi", "glm"}
