from fastapi import FastAPI, Request
from pydantic import BaseModel

from openai import OpenAI
from google import genai
from groq import Groq


# This file contains the FastAPI backend for handling chat requests to different LLM providers

# It includes:
# - run_llm function to route requests to the appropriate LLM based on provider
# - /chat endpoint to receive chat requests and return responses


from api.core.config import config # Import configuration for API keys so you dont have to hardcode them using os.environ

import logging 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# run_llm function to handle calls to different LLM providers based on input parameters, 
# connects to OpenAI, Google GenAI, or Groq APIbased on provider argument

def run_llm(provider, model_name, messages, max_tokens=500):

    if provider == "OpenAI":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
    elif provider == "Groq":
        client = Groq(api_key=config.GROQ_API_KEY)
    else:
        client = genai.Client(api_key=config.GOOGLE_API_KEY)

    if provider == "Google":
        return client.models.generate_content(
            model=model_name,
            contents=[message["content"] for message in messages],
        ).text
    elif provider == "Groq":
        return client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens
        ).choices[0].message.content
    else:
        return client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens,
            reasoning_effort="minimal"
        ).choices[0].message.content
    

# This is the request and response model for the /chat endpoint using Pydantic BaseModel for FastAPI data validation

# Define LLM request model for chat endpoint, intended to receive provider, model_name and chat history messages
class ChatRequest(BaseModel): 
    provider: str
    model_name: str
    messages: list[dict]

# Define LLM response model for chat endpoint
class ChatResponse(BaseModel): # Define response model for chat endpoint
    message : str

# Create FastAPI app instance
app = FastAPI() # Create FastAPI app instance


@app.post("/chat") # Define POST; HTTP method for endpoint to send a chat request to the backend
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    result = run_llm(
                        provider=payload.provider,
                        model_name=payload.model_name,
                        messages=payload.messages
                    )
    return ChatResponse(message=result)