import gi
gi.require_version("Secret", "1")

from gi.repository import Secret, GLib

APP_ID = "enhance-with-ai-openai"

SCHEMA = Secret.Schema.new(
    "enhance-with-ai-openai",
    Secret.SchemaFlags.NONE,
    {
        "application": Secret.SchemaAttributeType.STRING,
        "secret-type": Secret.SchemaAttributeType.STRING,
    },
)

ATTRIBUTES = {
    "application": APP_ID,
    "secret-type": "openai-api-key",
}


def get_api_key():
    """
    Retrieve the OpenAI API key from GNOME Keyring.
    Returns None if not found or unavailable.
    """
    try:
        secret = Secret.password_lookup_sync(
            SCHEMA,
            ATTRIBUTES,
            None,  # cancellable
        )
        return secret
    except GLib.Error:
        return None


def set_api_key(api_key: str):
    """
    Store (or replace) the OpenAI API key in GNOME Keyring.
    """
    Secret.password_store_sync(
        SCHEMA,
        ATTRIBUTES,
        Secret.COLLECTION_DEFAULT,
        "Enhance With AI – OpenAI API Key",
        api_key,
        None,  # cancellable
    )

