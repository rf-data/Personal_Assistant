from langfuse import get_client

langfuse = get_client()

# Create a span using a context manager
with langfuse.start_as_current_observation(
    as_type="span", name="process-request"
) as span:
    # Your processing logic here
    span.update(output="Processing complete")

    # Create a nested generation for an LLM call
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-response", model="gpt-3.5-turbo"
    ) as generation:
        # Your LLM call logic here
        generation.update(output="Generated response")

# All spans are automatically closed when exiting their context blocks

##############################################
# Flush events in short-lived applications
langfuse.flush()

from langfuse import observe


@observe()
def my_data_processing_function(data, parameter):
    return {"processed_data": data, "status": "ok"}


@observe(name="llm-call", as_type="generation")
async def my_async_llm_call(prompt_text):
    return "LLM response"


##############################################
from langfuse import get_client

langfuse = get_client()

span = langfuse.start_observation(name="manual-span")
span.update(input="Data for side task")
child = span.start_observation(name="child-span", as_type="generation")
child.end()
span.end()
