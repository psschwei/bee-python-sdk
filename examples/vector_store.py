"""
File Search tool usage

See OpenAI docs: https://platform.openai.com/docs/assistants/tools/file-search

COMPATIBILITY WARNING:
    - Batch file embedding is not implemented (client.beta.vector_stores.file_batches.*)
    - Message attachment embedding is not implemented
        (Each file must be embedded individually before using it as an attachment)
"""

import os
from pprint import pprint

from openai import OpenAI
from openai.types.beta import FileSearchToolParam


def heading(text: str) -> str:
    """Helper function for centering text."""
    return "\n" + f" {text} ".center(80, "=") + "\n"


client = OpenAI(api_key=os.getenv("BEE_API_KEY"), base_url=f'{os.getenv("BEE_API")}/v1')

print(heading("1. Upload a demo file"))
file_data = "Main character name is: The Bee!".encode("utf-8")
file = client.files.create(file=("story.txt", file_data), purpose="assistants")
print("File")
pprint(file.model_dump())

print(heading("2. Create a vector store and add the file"))
vector_store = client.beta.vector_stores.create(name="Bedtime story")
vector_store_file = client.beta.vector_stores.files.create_and_poll(file_id=file.id, vector_store_id=vector_store.id)
print("Vector store file")
pprint(vector_store_file.model_dump())

print(heading("3. Create assistant with vector store attached"))
assistant = client.beta.assistants.create(
    model="meta-llama/llama-3-1-70b-instruct",
    tools=[FileSearchToolParam(type="file_search")],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)
print("Assistant:")
pprint(assistant.model_dump())

print(heading("4. Create thread and run"))
thread = client.beta.threads.create(
    messages=[{"role": "user", "content": "Who is the main character according to the files?"}]
)
run = client.beta.threads.runs.create_and_poll(assistant_id=assistant.id, thread_id=thread.id)

if run.status != "completed":
    raise RuntimeError(f"Run is in an unexpected state: {run.status}\nError: {run.last_error}")

answer = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
print("Answer:", answer)

print(heading("5. (Advanced): Create a second vector store for 'thread-local' files"))
file_data = "Antagonist is: The Vasp!".encode("utf-8")
file_2 = client.files.create(file=("story2.txt", file_data), purpose="assistants")
thread_vector_store = client.beta.vector_stores.create(name="Bedtime story chapter 2")
vector_store_file = client.beta.vector_stores.files.create_and_poll(
    file_id=file_2.id,
    vector_store_id=thread_vector_store.id,
)
print("Vector store file")
pprint(vector_store_file.model_dump())

print(heading("6. (Advanced): Attach vector store to the thread"))
thread = client.beta.threads.update(
    thread.id, tool_resources={"file_search": {"vector_store_ids": [thread_vector_store.id]}}
)
print("Thread")
pprint(thread.model_dump())

print(heading("7. (Avanced): Add message and create run"))
client.beta.threads.messages.create(
    thread_id=thread.id,
    content="And who is the antagonist?",
    role="user",
    # Note: To add file_2 as attachment, you must first embed the file and add it to the thread vector store.
    # After that, the assistant can already access the file, so adding it as an attachment is optional:
    # attachments=[{"file_id": file_2.id, "tools": [{"type": "file_search"}]}],
)
run = client.beta.threads.runs.create_and_poll(assistant_id=assistant.id, thread_id=thread.id)

if run.status != "completed":
    raise RuntimeError(f"Run is in an unexpected state: {run.status}\nError: {run.last_error}")

answer = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
print("Answer:", answer)

# Cleanup
client.files.delete(file.id)
client.files.delete(file_2.id)
client.beta.threads.delete(thread.id)
client.beta.vector_stores.delete(vector_store.id)
client.beta.vector_stores.delete(thread_vector_store.id)
client.beta.assistants.delete(assistant.id)
