## observability.py
# import
import os

# from langfuse import Langfuse
import litellm
from pydantic_ai import Agent


def configure_llm_observability(env_vars) -> None:
    # Langfuse
    os.environ["LANGFUSE_PUBLIC_KEY"] = env_vars.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = env_vars.langfuse_secret_key

    # Falls du Langfuse Cloud EU verwendest bzw.
    # einen eigenen Host konfiguriert hast:
    if getattr(env_vars, "langfuse_host", None):
        os.environ["LANGFUSE_HOST"] = env_vars.langfuse_host

    # LiteLLM
    litellm.success_callback = ["langfuse"]

    # Pydantic AI / Marvin
    Agent.instrument_all()

    # return Langfuse()
