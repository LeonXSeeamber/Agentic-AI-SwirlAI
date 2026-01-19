import streamlit as st
from openai import OpenAI
from google import genai
from groq import Groq
from google.genai import types as genai_types
from core.config import config

@st.cache_resource
def get_clients():
    return {
        "OpenAI": OpenAI(api_key=config.OPENAI_API_KEY),
        "Groq": Groq(api_key=config.GROQ_API_KEY),
        "Google": genai.Client(api_key=config.GOOGLE_API_KEY),
    }

def run_llm(provider: str, model_name: str, messages, max_tokens: int = 500) -> str:
    try:
        clients = get_clients()
        client = clients[provider]

        if provider == "Google":
            # Separate system instruction from user content for GenAI API
            # Memory Injector: Only the first system message is used & only the last user message is used
            system_text = next((m["content"] for m in messages if m["role"] == "system"), "") 
            user_text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

            resp = client.models.generate_content(
                model=model_name,
                contents=[user_text],
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_text or "You are a helpful assistant."
                ),
            )
            return resp.text or ""

        if provider == "OpenAI":
            # Use Responses API for gpt-5-*
            resp = client.responses.create(
                model=model_name,
                input=messages, # Message history
                max_output_tokens=max_tokens,
                reasoning={"effort": "minimal"},
            )
            return resp.output_text or ""

        # Groq (OpenAI-compatible chat API)
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages, # Message history
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        st.error(f"Error: {e}")
        return f"Error encountered: {e}"


# Sidebar
with st.sidebar:
    st.title("Settings")
    provider = st.selectbox("Select LLM Provider", ["OpenAI", "Google", "Groq"])

    if provider == "OpenAI":
        model_name = st.selectbox("Select Model", ["gpt-5-nano", "gpt-5-mini", "gpt-4o", "gpt-4o-mini"])
    elif provider == "Groq":
        model_name = st.selectbox("Select Model", ["llama-3.3-70b-versatile", "llama-3.3-8b-instant"])
    else:
        model_name = st.selectbox("Select Model", ["gemini-2.5-flash"])

    st.session_state.provider = provider
    st.session_state.model_name = model_name


# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": "Hello! How can I assist you today?"},
    ]

# Render history
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Input + single model call
if prompt := st.chat_input("Type your message"): # 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run LLM to get assistant response
    with st.chat_message("assistant"):
        response = run_llm(
            provider=st.session_state.provider,
            model_name=st.session_state.model_name,
            messages=st.session_state.messages
        )
        st.markdown(response)

    # Add assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})