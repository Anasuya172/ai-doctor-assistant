from dotenv import load_dotenv
load_dotenv()

import os
import base64
from groq import Groq

# API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Default model
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# Encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# Analyze image/text query
def analyze_image_with_query(
    query,
    encoded_image=None,
    model=MODEL
):
    client = Groq(api_key=GROQ_API_KEY)

    # If image provided
    if encoded_image:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

    else:
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model
    )

    return chat_completion.choices[0].message.content