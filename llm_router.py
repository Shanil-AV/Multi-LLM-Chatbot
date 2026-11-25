from openai import OpenAI, RateLimitError
from config import PROVIDERS


def _is_rate_limit_error(exc):
    """Return True if an exception represents an HTTP 429 / rate-limit error."""
    if isinstance(exc, RateLimitError):
        return True
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "rate_limit" in msg


def _is_provider_usable(config):
    """Return True when a provider has credentials or allows keyless local access."""
    if not config or not config.get("models"):
        return False
    return bool(config.get("api_key") or (config.get("allow_empty_key") and config.get("base_url")))


def get_llm_response(provider, model, messages, provider_config=None):
    """Route a chat completion request to the selected OpenAI-compatible provider."""
    config = provider_config if provider_config is not None else PROVIDERS.get(provider)

    if not config:
        return f"Unknown provider: {provider}"

    if not model or not str(model).strip():
        return "Please select or enter a model."

    api_key = config.get("api_key")
    base_url = config.get("base_url")
    allow_empty_key = config.get("allow_empty_key", False)

    if not api_key:
        if allow_empty_key and base_url:
            # Local OpenAI-compatible servers (e.g. Ollama, LM Studio) accept a placeholder key
            api_key = "local-no-key"
        else:
            return f"API key not configured for {provider}"

    client_args = {"api_key": api_key}
    if base_url:
        client_args["base_url"] = base_url

    client = OpenAI(**client_args)

    response = client.chat.completions.create(
        model=str(model).strip(),
        messages=messages,
    )

    return response.choices[0].message.content


def get_llm_response_with_fallback(provider, model, messages, providers_map=None, auto_fallback=True):
    """Try the primary provider and fall back to other configured providers on rate limits."""
    catalog = providers_map if providers_map is not None else PROVIDERS
    primary_config = catalog.get(provider)

    try:
        answer = get_llm_response(provider, model, messages, provider_config=primary_config)
        return answer, provider, model, ""
    except Exception as primary_exc:
        if not auto_fallback or not _is_rate_limit_error(primary_exc):
            raise

        candidates = [
            (fb_name, fb_cfg["models"][0], fb_cfg)
            for fb_name, fb_cfg in catalog.items()
            if fb_name != provider and _is_provider_usable(fb_cfg)
        ]

        if not candidates:
            raise

        last_exc = primary_exc
        for fb_provider, fb_model, fb_cfg in candidates:
            try:
                answer = get_llm_response(fb_provider, fb_model, messages, provider_config=fb_cfg)
                notice = (
                    f"⚠️ `{provider}` hit a rate limit — automatically switched to "
                    f"**{fb_provider}** (`{fb_model}`)."
                )
                return answer, fb_provider, fb_model, notice
            except Exception as fb_exc:
                last_exc = fb_exc
                if _is_rate_limit_error(fb_exc):
                    continue
                raise

        raise last_exc
