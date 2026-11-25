import copy
import gradio as gr

from config import PROVIDERS, SYSTEM_MESSAGE
from llm_router import get_llm_response_with_fallback


# Default providers
default_providers = list(PROVIDERS.keys())

THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    radius_size="lg",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill="#f8fafc",
    body_background_fill_dark="#0b1120",
    background_fill_primary="#ffffff",
    background_fill_primary_dark="#111827",
    background_fill_secondary="#f1f5f9",
    background_fill_secondary_dark="#1e293b",
    block_background_fill="#ffffff",
    block_background_fill_dark="#111827",
    block_border_color="#e2e8f0",
    block_border_color_dark="#1f2937",
    border_color_primary="#e2e8f0",
    border_color_primary_dark="#334155",
)

CUSTOM_CSS = """
body,
gradio-app {
    background: var(--body-background-fill) !important;
    color: var(--body-text-color) !important;
    transition: background-color 0.2s ease, color 0.2s ease;
}

.gradio-container {
    max-width: 1220px !important;
    margin: 0 auto !important;
    padding: 20px 24px 28px !important;
}

#app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 22px;
    margin-bottom: 18px;
    border-radius: 16px;
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary);
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.dark #app-header {
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
}

#app-title h1 {
    margin: 0 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

#app-title p {
    margin: 4px 0 0 !important;
    font-size: 0.92rem !important;
    color: var(--body-text-color-subdued) !important;
}

#theme-toggle {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

#theme-toggle .wrap {
    display: inline-flex !important;
    flex-wrap: nowrap !important;
    gap: 4px !important;
    padding: 4px !important;
    border-radius: 9999px !important;
    background: var(--background-fill-secondary) !important;
    border: 1px solid var(--border-color-primary) !important;
}

#theme-toggle label {
    margin: 0 !important;
    padding: 6px 14px !important;
    border-radius: 9999px !important;
    border: none !important;
    background: transparent !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    white-space: nowrap !important;
}

#theme-toggle input[type="radio"] {
    display: none !important;
}

#theme-toggle label:has(input:checked) {
    background: var(--color-accent) !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.28) !important;
}

#settings-panel,
#chat-panel {
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary);
    border-radius: 16px;
    padding: 18px !important;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
}

.dark #settings-panel,
.dark #chat-panel {
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

#settings-heading h3 {
    margin: 0 0 6px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

#custom-accordion {
    border-radius: 12px !important;
    border: 1px solid var(--border-color-primary) !important;
}

#config-status p,
#route-status p {
    margin: 4px 0 0 !important;
    font-size: 0.84rem !important;
}

#chatbot-box {
    border-radius: 12px !important;
    border: 1px solid var(--border-color-primary) !important;
}

#chat-input {
    margin-top: 10px !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color-primary) !important;
    background: var(--background-fill-secondary) !important;
    padding: 4px 6px !important;
}

#action-row {
    margin-top: 6px !important;
    gap: 8px !important;
}

@media (max-width: 768px) {
    #app-header {
        flex-direction: column;
        align-items: flex-start;
    }
}
"""

INIT_THEME_JS = """
() => {
    const saved = localStorage.getItem("multi-llm-theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = saved ? saved === "dark" : prefersDark;
    const targets = [document.documentElement, document.body, document.querySelector("gradio-app")];
    targets.forEach((el) => {
        if (!el) return;
        el.classList.toggle("dark", isDark);
        el.style.colorScheme = isDark ? "dark" : "light";
    });
    return isDark ? "🌙 Dark" : "☀️ Light";
}
"""

APPLY_THEME_JS = """
(mode) => {
    const isDark = mode === "🌙 Dark";
    localStorage.setItem("multi-llm-theme", isDark ? "dark" : "light");
    const targets = [document.documentElement, document.body, document.querySelector("gradio-app")];
    targets.forEach((el) => {
        if (!el) return;
        el.classList.toggle("dark", isDark);
        el.style.colorScheme = isDark ? "dark" : "light";
    });
}
"""

ERROR_PREFIX = "⚠️ Error: "


def change_provider(provider, providers_state):
    """Update model dropdown choices when the selected provider changes."""
    cfg = (providers_state or PROVIDERS).get(provider, {})
    models = cfg.get("models", [])
    return gr.Dropdown(
        choices=models,
        value=models[0] if models else None,
    )


def add_model_to_provider(provider, new_model, providers_state):
    """Add a custom model ID to the currently selected provider in session state."""
    state = copy.deepcopy(providers_state or PROVIDERS)
    model_id = (new_model or "").strip()

    if not provider or provider not in state:
        return state, gr.skip(), new_model, "⚠️ Select a valid provider first."

    if not model_id:
        return state, gr.skip(), new_model, "⚠️ Enter a model ID to add."

    models = state[provider].setdefault("models", [])
    if model_id in models:
        return (
            state,
            gr.Dropdown(choices=models, value=model_id),
            "",
            f"ℹ️ `{model_id}` is already in **{provider}** (selected).",
        )

    models.append(model_id)
    return (
        state,
        gr.Dropdown(choices=models, value=model_id),
        "",
        f"✅ Added `{model_id}` to **{provider}**.",
    )


def add_custom_provider(name, base_url, api_key, models_text, providers_state):
    """Add or update an OpenAI-compatible custom provider in session state."""
    state = copy.deepcopy(providers_state or PROVIDERS)
    provider_name = (name or "").strip()
    cleaned_url = (base_url or "").strip()
    cleaned_key = (api_key or "").strip()

    raw_models = (models_text or "").replace("\n", ",").split(",")
    parsed_models = list(dict.fromkeys(m.strip() for m in raw_models if m.strip()))

    if not provider_name:
        return state, gr.skip(), gr.skip(), name, base_url, api_key, models_text, "⚠️ Enter a provider name."

    if not parsed_models:
        return (
            state,
            gr.skip(),
            gr.skip(),
            name,
            base_url,
            api_key,
            models_text,
            "⚠️ Enter at least one model ID (comma-separated).",
        )

    if cleaned_url and not cleaned_url.startswith(("http://", "https://")):
        return (
            state,
            gr.skip(),
            gr.skip(),
            name,
            base_url,
            api_key,
            models_text,
            "⚠️ Base URL must start with `http://` or `https://`.",
        )

    if provider_name in state:
        existing = state[provider_name]
        merged_models = list(dict.fromkeys([*existing.get("models", []), *parsed_models]))
        state[provider_name] = {
            "api_key": cleaned_key or existing.get("api_key"),
            "base_url": cleaned_url or existing.get("base_url"),
            "models": merged_models,
            "allow_empty_key": existing.get("allow_empty_key", False) or bool(cleaned_url),
        }
        status = f"✅ Updated **{provider_name}** with {len(parsed_models)} model(s)."
    else:
        if not cleaned_url and not cleaned_key:
            return (
                state,
                gr.skip(),
                gr.skip(),
                name,
                base_url,
                api_key,
                models_text,
                "⚠️ Provide an API key or an OpenAI-compatible Base URL.",
            )
        state[provider_name] = {
            "api_key": cleaned_key or None,
            "base_url": cleaned_url or None,
            "models": parsed_models,
            "allow_empty_key": bool(cleaned_url),
        }
        status = f"✅ Added provider **{provider_name}** ({len(parsed_models)} model(s))."

    provider_dd = gr.Dropdown(choices=list(state.keys()), value=provider_name)
    model_dd = gr.Dropdown(choices=state[provider_name]["models"], value=parsed_models[0])
    return state, provider_dd, model_dd, "", "", "", "", status


def _extract_text(content):
    """Normalize Gradio Chatbot message content to a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part)
    return str(content) if content is not None else ""


def _build_llm_messages(history, system_message):
    """Convert Gradio chat history into clean OpenAI-format messages, skipping error turns."""
    messages = []
    if system_message and system_message.strip():
        messages.append({"role": "system", "content": system_message})

    for entry in history:
        role = entry.get("role") if isinstance(entry, dict) else getattr(entry, "role", None)
        raw_content = entry.get("content") if isinstance(entry, dict) else getattr(entry, "content", "")
        text_content = _extract_text(raw_content)
        if not text_content or role not in ("user", "assistant", "system"):
            continue
        if role == "assistant" and text_content.startswith(ERROR_PREFIX):
            continue
        messages.append({"role": role, "content": text_content})

    return messages


def add_user_message(message, history):
    """Append the user's message immediately and clear the input box."""
    history = list(history or [])
    if not message or not message.strip():
        return "", history
    history.append({"role": "user", "content": message})
    return "", history


def generate_reply(history, provider, model, system_message, providers_state, auto_fallback=True):
    """Generate an assistant response for the latest user turn, with optional rate-limit fallback."""
    history = list(history or [])
    if not history:
        return history, ""

    last_role = history[-1].get("role") if isinstance(history[-1], dict) else getattr(history[-1], "role", None)
    if last_role != "user":
        return history, ""

    messages = _build_llm_messages(history, system_message)
    state = providers_state or PROVIDERS
    notice = ""

    try:
        answer, used_provider, used_model, notice = get_llm_response_with_fallback(
            provider,
            model,
            messages,
            providers_map=state,
            auto_fallback=bool(auto_fallback),
        )
        if not notice and used_provider == provider:
            notice = f"Answered by **{used_provider}** (`{used_model}`)."
    except Exception as e:
        answer = f"{ERROR_PREFIX}{str(e)}"
        notice = "⚠️ Request failed. Switch provider/model and click **🔄 Retry Last**."

    history.append({"role": "assistant", "content": answer})
    return history, notice


def retry_last_message(history, provider, model, system_message, providers_state, auto_fallback=True):
    """Drop the latest assistant turn (e.g. a rate-limit error) and re-run the last user message."""
    history = list(history or [])
    if not history:
        return history, "ℹ️ Nothing to retry yet."

    last_role = history[-1].get("role") if isinstance(history[-1], dict) else getattr(history[-1], "role", None)
    if last_role == "assistant":
        history = history[:-1]

    if not history:
        return history, "ℹ️ No user message found to retry."

    return generate_reply(history, provider, model, system_message, providers_state, auto_fallback)


# Gradio UI
with gr.Blocks(title="Multi-LLM Chatbot") as demo:
    providers_state = gr.State(lambda: copy.deepcopy(PROVIDERS))

    with gr.Row(elem_id="app-header"):
        with gr.Column(scale=4, elem_id="app-title"):
            gr.Markdown(
                "# Multi-LLM Chatbot\n"
                "Chat seamlessly across Groq, Gemini, OpenRouter, OpenAI, or your own custom endpoints."
            )
        theme_mode = gr.Radio(
            choices=["☀️ Light", "🌙 Dark"],
            value="☀️ Light",
            show_label=False,
            container=False,
            interactive=True,
            elem_id="theme-toggle",
        )

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=300, elem_id="settings-panel"):
            gr.Markdown("### Model & Prompt", elem_id="settings-heading")

            provider = gr.Dropdown(
                choices=default_providers,
                value=default_providers[0],
                label="Provider",
            )

            model = gr.Dropdown(
                choices=PROVIDERS[default_providers[0]]["models"],
                value=PROVIDERS[default_providers[0]]["models"][0],
                label="Model",
                info="Pick a model or type any custom model ID.",
                allow_custom_value=True,
            )

            auto_fallback = gr.Checkbox(
                label="Auto-fallback on rate limit",
                value=True,
                info="Automatically try another configured provider if HTTP 429 occurs.",
            )

            with gr.Accordion("➕ Add Custom Model / Provider", open=False, elem_id="custom-accordion"):
                gr.Markdown("**Add a model to the selected provider**")
                new_model_input = gr.Textbox(
                    label="Model ID",
                    placeholder="e.g. gpt-4.1-mini or llama-3.1-8b-instant",
                )
                add_model_btn = gr.Button("Add Model", variant="secondary", size="sm")

                gr.Markdown("---\n**Add an OpenAI-compatible provider**")
                custom_provider_name = gr.Textbox(
                    label="Provider Name",
                    placeholder="e.g. Ollama, DeepSeek, Together",
                )
                custom_base_url = gr.Textbox(
                    label="OpenAI-Compatible Base URL",
                    placeholder="e.g. http://localhost:11434/v1",
                )
                custom_api_key = gr.Textbox(
                    label="API Key",
                    type="password",
                    placeholder="Optional for local endpoints like Ollama",
                )
                custom_provider_models = gr.Textbox(
                    label="Model ID(s)",
                    placeholder="Comma-separated, e.g. llama3.2, qwen2.5",
                )
                add_provider_btn = gr.Button("Add Provider", variant="primary", size="sm")
                config_status = gr.Markdown("", elem_id="config-status")

            system_message = gr.Textbox(
                label="System Prompt",
                value=SYSTEM_MESSAGE,
                lines=4,
                max_lines=8,
                placeholder="Set the assistant's behavior or persona...",
            )

            with gr.Row(elem_id="action-row"):
                retry_btn = gr.Button("🔄 Retry Last", variant="secondary")
                clear = gr.Button("🗑️ Clear Chat", variant="secondary")

        with gr.Column(scale=3, min_width=420, elem_id="chat-panel"):
            chatbot = gr.Chatbot(
                label="AI Chat",
                show_label=False,
                height=520,
                buttons=["copy", "copy_all"],
                placeholder=(
                    "### Start a conversation\n"
                    "Select a provider and model on the left (or add your own), then ask anything below."
                ),
                elem_id="chatbot-box",
            )

            route_status = gr.Markdown("", elem_id="route-status")

            msg = gr.Textbox(
                placeholder="Type a message and press Enter...",
                show_label=False,
                container=False,
                submit_btn=True,
                autofocus=True,
                lines=1,
                max_lines=6,
                elem_id="chat-input",
            )

            gr.Examples(
                examples=[
                    "Explain quantum computing in simple terms.",
                    "Write a clean Python script to summarize a CSV file.",
                    "Give me 5 creative productivity tips for software engineers.",
                ],
                inputs=msg,
                label="Quick Prompts",
            )

    # Apply saved or system theme on page load and on toggle
    demo.load(
        fn=None,
        inputs=None,
        outputs=theme_mode,
        js=INIT_THEME_JS,
    )

    theme_mode.input(
        fn=None,
        inputs=theme_mode,
        outputs=None,
        js=APPLY_THEME_JS,
    )

    # Change model list when provider changes
    provider.change(
        fn=change_provider,
        inputs=[provider, providers_state],
        outputs=model,
    )

    # Add a model to the selected provider
    add_model_btn.click(
        fn=add_model_to_provider,
        inputs=[provider, new_model_input, providers_state],
        outputs=[providers_state, model, new_model_input, config_status],
    )

    # Add or update a custom provider
    add_provider_btn.click(
        fn=add_custom_provider,
        inputs=[
            custom_provider_name,
            custom_base_url,
            custom_api_key,
            custom_provider_models,
            providers_state,
        ],
        outputs=[
            providers_state,
            provider,
            model,
            custom_provider_name,
            custom_base_url,
            custom_api_key,
            custom_provider_models,
            config_status,
        ],
    )

    # Send message immediately to chat, then generate assistant reply
    msg.submit(
        fn=add_user_message,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False,
    ).then(
        fn=generate_reply,
        inputs=[chatbot, provider, model, system_message, providers_state, auto_fallback],
        outputs=[chatbot, route_status],
    )

    # Retry last prompt with current provider/model
    retry_btn.click(
        fn=retry_last_message,
        inputs=[chatbot, provider, model, system_message, providers_state, auto_fallback],
        outputs=[chatbot, route_status],
    )

    # Clear conversation
    clear.click(
        fn=lambda: ([], ""),
        outputs=[chatbot, route_status],
    )


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CUSTOM_CSS,share=True)
