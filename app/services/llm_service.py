from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant" # Use a standard Groq model

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name=MODEL,
    temperature=0
)

vision_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0
)

def call_llm(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content

import base64
from langchain_core.messages import HumanMessage

def call_vision_llm(prompt: str, image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Check extension
    ext = image_path.split('.')[-1].lower()
    mime_type = "image/jpeg"
    if ext == "png":
        mime_type = "image/png"
    elif ext in ["jpg", "jpeg"]:
        mime_type = "image/jpeg"
    elif ext == "webp":
        mime_type = "image/webp"

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}}
        ]
    )
    response = vision_llm.invoke([message])
    return response.content