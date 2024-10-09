"""
Function Calling

Define python functions and execute them locally, when the assistant asks for it.

See OpenAI docs: https://platform.openai.com/docs/assistants/tools/function-calling
"""

import inspect
import json
import os

import requests
from openai import OpenAI


def heading(text: str) -> str:
    """Helper function for centering text."""
    return "\n" + f" {text} ".center(80, "=") + "\n"


client = OpenAI(api_key=os.getenv("BEE_API_KEY"), base_url=f'{os.getenv("BEE_API")}/v1')


def ip_info(ip: str) -> dict:
    """
    Get information about an IP address, such as location, company, and carrier name.

    :param ip: IP address in the 255.255.255.255 format
    :return: Information about the IP address
    """
    response = requests.get(f"https://ipinfo.io/{ip}/geo")
    response.raise_for_status()
    return response.json()


assistant = client.beta.assistants.create(
    instructions="You are IP address analytic. Use the provided functions to get info about IP address.",
    model="meta-llama/llama-3-1-70b-instruct",
    tools=[
        {
            "type": "function",
            "function": {
                "name": ip_info.__name__,
                "description": inspect.getdoc(ip_info).split("\n")[0],
                "parameters": {
                    "type": "object",
                    "properties": {"ip": {"type": "string", "description": "IP address in the 255.255.255.255 format"}},
                    "required": ["ip"],
                },
            },
        },
    ],
)
thread = client.beta.threads.create(messages=[{"role": "user", "content": "Who owns the IP 8.8.8.8?"}])
run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant.id)

while run.status == "requires_action":
    tool_outputs = []
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == ip_info.__name__:
            ip = json.loads(tool.function.arguments)["ip"]
            tool_outputs.append({"tool_call_id": tool.id, "output": json.dumps(ip_info(ip))})

    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
    )

if run.status != "completed":
    raise RuntimeError(f"Run is in an unexpected state: {run.status}\nError: {run.last_error}")
else:
    answer = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
    print("Answer:", answer)

# Cleanup
client.beta.threads.delete(thread.id)
client.beta.assistants.delete(assistant.id)
