import os
import openai
from dotenv import find_dotenv, load_dotenv

load_dotenv()

open_ai_secret = os.getenv("OPEN_AI_SECRET")

name = ("SMS Rephraser",)
client = openai.OpenAI(api_key=open_ai_secret)
model = "gpt-3.5-turbo"

# prompt = (
#     "You are a SMS rephraser assistant. Your goal is to provide polite and concise rephrased versions of user messages. "
#     "Keep the responses clear and respectful. Provide a few alternative suggestions. "
#     "User: \"I will come back soon.\""
# )

prompt = (
    """As a real-time SMS rephraser assistant, your objective is to enhance the clarity and appropriateness of user messages. 
    Your responses should be polite, concise, and offer multiple alternative suggestions. 
    Your task is to analyze incoming text inputs and provide real-time suggestions for alternative phrasings. 
    Users may accept, reject, or ignore your suggestions."""
)

# response = client.chat.completions.create(
#     model=model,
#     messages=[
#         {"role": "system", "content": prompt},
#         {"role": "user", "content": "I will come back soon."},
#     ],
#     max_tokens=50,
#     stop=None
# )


# for choice in response.choices:
#     message = choice.message
#     # print(f"Suggestion {choice.index+1}")
#     print(f"{message.content}")


stream = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": "I will come back soon."},
    ],
    max_tokens=50,
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
