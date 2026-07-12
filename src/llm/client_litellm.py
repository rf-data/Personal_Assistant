## client.py
# imports
import litellm

from src.core.memory import LLMContext


## install Litellm
# curl -fsSL https://raw.githubusercontent.com/BerriAI/litellm/main/scripts/install.sh | sh

# Logging 
# litellm.success_callback = ["langfuse", "mlflow", "helicone"]
# response = litellm.completion(
#   model="gpt-4o",
#   messages=[{"role": "user", "content": "Hi!"}]
# )

# track costs & usuage
# def track_cost(kwargs, completion_response, start_time, end_time):
#     print("Cost:", kwargs.get("response_cost", 0))

# litellm.success_callback = [track_cost]

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

class LLMClient:

    def generate(
        self,
        messages,
        llm_context: LLMContext
        ):
        ...
        model=llm_context.model, # "gpt-5",
        temperature=llm_context.temperature   # 0.2,
    
        return 

# --> client.generate(...)