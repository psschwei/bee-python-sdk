"""Basic conversation with an assistant that generates a file"""

import os
import re
from pprint import pprint

from openai import OpenAI


def heading(text: str) -> str:
    """Helper function for centering text."""
    return "\n" + f" {text} ".center(80, "=") + "\n"


client = OpenAI(api_key=os.getenv("BEE_API_KEY"), base_url=f'{os.getenv("BEE_API")}/v1')

print(heading("Create assistant with code_interpreter tool enabled."))
assistant = client.beta.assistants.create(
    model="meta-llama/llama-3-1-70b-instruct", tools=[{"type": "code_interpreter"}]
)
print("Assistant:")
pprint(assistant.model_dump())

print(heading("Run model and get answer"))
thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "Generate first 10 fibonacci numbers and save them to fibonacci.txt",
        }
    ]
)
run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant.id)
messages = client.beta.threads.messages.list(thread_id=thread.id)
answer = messages.data[0].content[0].text.value
print("Answer:", answer)

# Parse generated file_id from answer
file_id_match = re.match(r".*urn:bee:file:([^)]*)", answer)
file_id = file_id_match and file_id_match.group(1)
if not file_id:
    raise RuntimeError("Assistant did not generate a file")

print(heading("Download generated attachments"))
file = client.files.retrieve(file_id)
file_content = client.files.content(file_id).text

print("File:")
pprint(file.model_dump())

print("File content:")
print(file_content)

# Cleanup
client.beta.threads.delete(thread.id)
client.beta.assistants.delete(assistant.id)
