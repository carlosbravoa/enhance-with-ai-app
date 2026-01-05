from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "enhance-with-ai"
CONFIG_FILE = CONFIG_DIR / "config"
DEFAULT_MODEL = "gpt-4o-mini"

TEMPLATE = """# Enhance With AI – configuration file
# Required:
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional (defaults to gpt-4o-mini if missing)
MODEL=gpt-4o-mini
"""

class ConfigError(Exception):
    pass

def load_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(TEMPLATE)
        raise ConfigError(
            f"Configuration file created at:\n\n{CONFIG_FILE}\n\n"
            "Please add your OpenAI API key and restart the app."
        )

    api_key = None
    model = DEFAULT_MODEL

    for line in CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        if key == "OPENAI_API_KEY":
            api_key = value
        elif key == "MODEL":
            model = value

    if not api_key:
        raise ConfigError("OPENAI_API_KEY is missing in the config file")

    return api_key, model
