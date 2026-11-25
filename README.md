# Multi-LLM Chatbot

A clean, modern multi-provider AI chat workspace built with **Python**, **Gradio 6**, and the **OpenAI SDK**. Switch between Groq, Google Gemini, OpenRouter, OpenAI, or your own OpenAI-compatible endpoints (including local servers like Ollama and LM Studio) from a single interface.

## Features

- **Multi-Provider Switching**: Switch seamlessly between built-in providers and models from the sidebar.
- **Custom Models & Providers**:
  - Type any model ID directly in the `Model` dropdown (`allow_custom_value=True`).
  - Add new models to existing providers or register custom **OpenAI-compatible** providers (such as Ollama, LM Studio, DeepSeek, or Together AI) per browser session via the **`➕ Add Custom Model / Provider`** accordion.
  - Supports keyless local endpoints when a `Base URL` is provided.
- **Rate-Limit Resilience**:
  - **Auto-fallback on rate limit**: Automatically retries with another configured provider when HTTP `429` / rate-limit errors occur.
  - **🔄 Retry Last**: Switch providers/models at any time and re-run the last prompt without retyping (previous failed error bubbles are stripped automatically).
- **Light / Dark Mode Switch**: Built-in header toggle (`☀️ Light` / `🌙 Dark`) with system-preference fallback and `localStorage` persistence.
- **Responsive Chat Workspace**:
  - Editable **System Prompt**
  - Multi-turn conversation history with instant user message rendering
  - Copy message / copy all buttons, clear conversation button, and quick starter prompts

## Built-in Providers & Models

Configured in `config.py`:

| Provider | Environment Variable | Default Models |
| --- | --- | --- |
| **Groq** | `GROQ_API_KEY` | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `llama-3.3-70b-versatile` |
| **Gemini** | `GEMINI_API_KEY` | `gemini-2.5-flash`, `gemini-2.5-pro` |
| **OpenRouter** | `OPENROUTER_API_KEY` | `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1`, `qwen/qwen3-235b-a22b` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` |

## Project Structure

```text
chatbot/
├── app.py          # Gradio 6 UI, theming, Light/Dark mode toggle, and session state
├── config.py       # Built-in provider configs, base URLs, models, and default system prompt
├── llm_router.py   # Unified OpenAI-compatible chat completion router
├── .env            # API keys (not committed to version control)
└── README.md
```

## Setup & Installation

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install gradio openai python-dotenv
   ```

3. **Configure API keys**

   Create a `.env` file in the project root and add keys for the providers you want to use:
   ```env
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Run the app**
   ```bash
   .venv/bin/python app.py
   ```
   Then open the local URL printed in the terminal (by default `http://127.0.0.1:7860`).

## Adding Custom Providers in the UI

Open **`➕ Add Custom Model / Provider`** in the left sidebar:
- **Add Model**: Enter a model ID and click **Add Model** to append it to the currently selected provider.
- **Add Provider**: Enter a provider name, an OpenAI-compatible `Base URL` (for example `http://localhost:11434/v1` for Ollama), an optional `API Key`, and comma-separated model IDs (for example `llama3.2, qwen2.5`).

> **Note:** Custom providers and API keys entered in the UI are stored only in your active Gradio session (`gr.State`) and are not written to disk.

