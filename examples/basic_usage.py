"""Basic conversation with an assistant"""

import os
from pprint import pprint

from openai import OpenAI


def heading(text: str) -> str:
    """Helper function for centering text."""
    return "\n" + f" {text} ".center(80, "=") + "\n"


# Instantiate OpenAI client with Bee credentials from env
client = OpenAI(base_url=f'{os.getenv("BEE_API")}/v1', api_key=os.getenv("BEE_API_KEY"))

print(heading("Create assistant"))
assistant = client.beta.assistants.create(
    model="meta-llama/llama-3-1-70b-instruct", tools=[{"type": "code_interpreter"}]
)
print("Assistant:")
pprint(assistant.model_dump())

print(heading("Create a thread with user message"))
question = "What is the unicode character U+1F41D? Create a haiku about it."
thread = client.beta.threads.create(messages=[{"role": "user", "content": question}])

print(heading("Create a run and wait for completion"))
run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant.id)
assert run.status == "completed"
print("Run:")
pprint(run.model_dump())

print(heading("Get an answer"))
messages = client.beta.threads.messages.list(thread_id=thread.id)
print("Answer:", messages.data[0].content[0].text.value)

# Cleanup
client.beta.assistants.delete(assistant_id=assistant.id)
