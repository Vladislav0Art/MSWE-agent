from langfuse._client.client import Langfuse
from langfuse import get_client

from sweagent.utils.config import keys_config
from sweagent.utils.other import is_true

_langfuse = None

def tracing_enabled() -> bool:
    trace_to_langfuse = keys_config.get("TRACE_TO_LANGFUSE", False)
    return is_true(trace_to_langfuse)

def configure_langfuse():
    """Creates or gets a Langfuse instance

        Requires the following variables in the ``keys_config``:
          - LANGFUSE_HOST
          - LANGFUSE_SECRET_KEY
          - LANGFUSE_PUBLIC_KEY
    """
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse(
            secret_key=keys_config["LANGFUSE_SECRET_KEY"],
            public_key=keys_config["LANGFUSE_PUBLIC_KEY"],
            host=keys_config["LANGFUSE_HOST"],
        )
        _langfuse.auth_check()


def get_langfuse_client_if_enabled() -> Langfuse | None:
    trace_to_langfuse = tracing_enabled()
    if is_true(trace_to_langfuse):
        print("Trace to Langfuse is enabled")
        configure_langfuse()
        langfuse = get_client(public_key=keys_config["LANGFUSE_PUBLIC_KEY"])
    else:
        langfuse = None
    return langfuse
