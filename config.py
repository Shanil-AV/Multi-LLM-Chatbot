import os
from dotenv import load_dotenv

load_dotenv(override=True)

PROVIDERS = {
    "Groq": {
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile"
        ]
    },

    "Gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro"
        ]
    },

    "OpenRouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-r1",
            "qwen/qwen3-235b-a22b"
        ]
    },

    "OpenAI": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": None,
        "models": [
            "gpt-4o-mini"
        ]
    }
}

SYSTEM_MESSAGE = "You are a helpful AI assistant."