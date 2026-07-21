## model_litellm.py
# imports
from __future__ import annotations

import csv
from datetime import datetime
from typing import Any

import instructor
import litellm

from src.core.logger import create_logger
from src.core.memory import LLMContext
from src.utils.general_helper import load_from_cache, make_cache_key


class LLMClient:
    def __init__(self, llm_context: LLMContext):
        self.context = llm_context
        self.model = llm_context.model  # "gpt-5",
        self.temperature = llm_context.temperature
        self.response_model = llm_context.response_model

        return

    def __post_init__(self):
        log_name = self.context.name_logger
        name_logfile = self.context.name_logfile
        today = datetime.today().strftime("%Y-%m-%d")

        self.logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")

        self.client = instructor.from_provider(f"litellm/{self.model}")
        self._configure_callbacks()

        return

    def completion(self, messages: list[dict[str, Any]], **kwargs):
        """
        Gibt das vollständige LiteLLM-Response-Objekt zurück.
        """
        cached_complete = self._cache_available(messages)

        if cached_complete is not None:
            return cached_complete

        client = ""
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            **kwargs,
        )

        self._track_costs(kwargs, response, start_time=str(datetime.now()))

        return response

    """
    ## Non-stream ResponseModel 'completion()'
    {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-4o",
    "choices": [
        {
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "Hello! I'm doing well, thanks for asking."
        },
        "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 12,
        "total_tokens": 25
    }
    }
    """

    def generate(
        self,
        messages,
        **kwargs,
    ) -> str:
        """
        Gibt nur den generierten Text zurück.
        """
        response = self.completion(
            messages=messages,
            **kwargs,
        )

        return response.choices[0].message.content

    def _cache_available(self, message):
        key = make_cache_key(message=message, model=self.model)
        cached = load_from_cache(key=key, folder=self.model)

        if cached is not None:
            return cached

        return None

    def _configure_callbacks(self) -> None:
        """
        Konfiguriert optionale LiteLLM-Callbacks.
        """

        callbacks = getattr(
            self.context,
            "callbacks",
            None,
        )

        if self.context.callbacks:
            litellm.success_callback = callbacks

    def _track_costs(
        self,
        kwargs,  # kwargs to completion
        completion_response,  # response from completion
        start_time="n.a.",
        end_time="n.a.",  # start/end time
    ):
        """
        Beispiel für einen Custom Success Callback.
        """
        response_cost = kwargs.get("response_cost", "n.a.")
        model = completion_response.get("model", "n.a.")
        usuage = completion_response.get("usuage", "n.a.")
        """
        if response_cost is None:
            return
        """
        self.logger.info(
            "model used: %s\nstart | end time: %s | %susuage: \n%s\nLLM cost: %s",
            model,
            start_time,
            end_time,
            usuage,
            response_cost,
        )

        f_path = self.context.path_tracker_file
        data = [model, start_time, end_time, usuage, response_cost]

        with open(f_path, "a", newline="\n", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)

        return None

        # try:
        #     response_cost = kwargs.get("response_cost", 0)
        #     print("streaming response_cost", response_cost)
        # except:
        #     pass

        # # set callback
        # litellm.success_callback = [track_cost_callback]

        # return


## install Litellm
# curl -fsSL https://raw.githubusercontent.com/BerriAI/litellm/main/scripts/install.sh | sh

# Logging


# track costs & usuage


# litellm.completion(
#   model="gpt-4o",
#   messages=[{"role": "user", "content": "Hello!"}],
#   stream=True
# )

# Call it with the OpenAI client
# import openai

# client = openai.OpenAI(api_key="anything", base_url="http://0.0.0.0:4000")

# response = client.chat.completions.create(
#   model="gpt-3.5-turbo",
#   messages=[{"role": "user", "content": "Write a short poem"}]
# )
# print(response.choices[0].message.content)


# --> client.generate(...)
