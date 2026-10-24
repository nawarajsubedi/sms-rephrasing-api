# NOTE: standalone OpenAI-only experiment. It talks to the OpenAI SDK directly
# (needs OPEN_AI_SECRET) and does not use the app. To try Bedrock, run the API
# and call POST /v2/message/rephrase.
import json
import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPEN_AI_SECRET")

openai_client = openai.OpenAI(api_key=openai_api_key)
model = "gpt-3.5-turbo"


def generate_auto_reply_suggestions(conversation_history):
    # Prompt for the AI model
    prompt = """
    You are building a VoIP solution and seeking suggestions for auto-reply based on the last conversation history provided by the customer. 
    Your task is to analyze the previous conversation history and provide helpful suggestions for replies.

    Objective:
    Your objective is to provide real-time suggestions based on the previous conversations to improve the clarity and appropriateness of user messages.

    Instructions:
    1. Analyze the provided conversation history for context of two persons conversation.
    2. Generate auto-reply a fews suggestions options(3-5 max) based on the analyzed context.
    3. Ensure that the suggested replies enhance clarity and are appropriate for the conversation.
    4. Choose and customize any of the suggestions for your response.
    5. Please provide auto-reply suggestions without additional instructions or headers.
    6. Please do not send reply using one line instead return in json array so we can direclty show to end user in auto-suggestion options.
    """

    # Generate auto-reply suggestions from OpenAI API
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": conversation_history},
        ],
        temperature=0.7,
        max_tokens=150,
        # n=5,  # Number of suggestions to generate
        stop=None,  # Stop generating suggestions when reaching this token
    )

    # Extract and return auto-reply suggestions
    auto_reply_suggestions = []
    for choice in response.choices:
        suggestion_content = choice.message.content
        auto_reply_suggestions.append(suggestion_content)

    return auto_reply_suggestions


# Example usage
customer_conversation_history = [
    """
    Person 1: How'd the team react to the new laptops?
    Person 2: Mostly positive, though some voiced concerns about pricing.
    """,
    """
    Person 1: Any standout criticisms or suggestions?
    Person 2: Suggestions for better marketing and customization options stood out.
    """,
    """
    Person 1: Any concerns about the design or features?
    Person 2: Yes, some mentioned the need for more durability.
    """,
]

conversation_history_text = "\n".join(customer_conversation_history)
final_results = []
auto_reply_suggestions = generate_auto_reply_suggestions(conversation_history_text)
# print("Auto-reply suggestions:->\n", auto_reply_suggestions)
for i, suggestion in enumerate(auto_reply_suggestions, 1):
    final_results = json.loads(suggestion)
    # print(f"{suggestion}")

print("-----------------final_results------------------")

if isinstance(final_results, list) and len(final_results):
    for item in final_results:
        print(item)
