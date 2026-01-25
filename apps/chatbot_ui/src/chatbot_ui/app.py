import streamlit as st
from chatbot_ui.core.config import config
import requests

#

# This function is a resilient HTTP client for your Streamlit app that dynamically calls an API, 
# safely parses responses, handles network failures, and surfaces user-friendly errors via Streamlit state.

# Its job is to :
# . Call your FastAPI backend or any other API endpoint using requests library e.g. method = "get" or "post" -> response = requests.get(url) or requests.post(url)
# . Handle errors like connection issues, timeouts, unexpected errors
# . Show user friendly error popups in the UI when something goes wrong
# . Return success status and response data to the caller in a tuple (success, data)
def api_call(method, url, **kwargs):

    # Writes error message into st.session_state, st.session_state is a history of all variables in a streamlit app session e.g. 'error_popup', 'messages', 'provider', 'model_name'
    def _show_error_popup(message):
        """Show error message as a popup in the top-right corner."""
        st.session_state["error_popup"] = {
            "visible": True,
            "message": message,
        }

    # Validate HTTP method against an allowed list to prevent arbitrary attribute access on the requests module
    allowed_methods = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
        "delete": requests.delete,
        "patch": requests.patch,
        "head": requests.head,
        "options": requests.options,
    }
    method_name = method.lower()
    if method_name not in allowed_methods:
        _show_error_popup(f"Unsupported HTTP method: {method}")
        return False, {"message": "Unsupported HTTP method"}
        # For non-2xx responses, show an error popup and return False with response data (which may contain error details

    try:
        response = allowed_methods[method_name](url, **kwargs) # Dynamically chooses requests method, **kwargs allows passing additional arguments like headers, json, data, params etc.

        # Deal with JSON decode errors separately
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError: # Gracefully handle JSON decode errors
            response_data = {"message": "Invalid response format from server"}

        if response.ok: # If response status code is 200-299, case the request was successful but server returned non-JSON response
            return True, response_data

        return False, response_data # For non-2xx responses, return False with response data (which may contain error details) 

    # Handle specific request exception errors
    except requests.exceptions.ConnectionError:
        _show_error_popup("Connection error. Please check your network connection.")
        return False, {"message": "Connection error"}
    except requests.exceptions.Timeout:
        _show_error_popup("The request timed out. Please try again later.")
        return False, {"message": "Request timeout"}
    except Exception as e:
        _show_error_popup(f"An unexpected error occurred: {str(e)}")
        return False, {"message": str(e)}


# Sidebar
with st.sidebar:
    st.title("Settings")
    provider = st.selectbox("Select LLM Provider", ["OpenAI", "Google", "Groq"])

    if provider == "OpenAI":
        model_name = st.selectbox("Select Model", ["gpt-5-nano", "gpt-5-mini"])
    elif provider == "Groq":
        model_name = st.selectbox("Select Model", ["llama-3.3-70b-versatile","llama-3.3-8b-instant"])
    else:
        model_name = st.selectbox("Select Model", ["gemini-2.5-flash"])

    st.session_state.provider = provider
    st.session_state.model_name = model_name


# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
#        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": "Hello! How can I assist you today?"}
    ]

# Render history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


# If user inputs a prompt
# Add user message to session state and display it in chat using st.chat_message visual container and st.markdown to render markdown content

if prompt := st.chat_input("Type your message"): # 
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Create visual container in chat interface for user message
    with st.chat_message("user"):
        st.markdown(prompt) # Display user message in chat interface

    # Create visual container in chat interface for assistant message
    with st.chat_message("assistant"):

        # Call API to get assistant response giving it provider, model_name and chat history messages
        # response = api_call(
        #                         method="post", 
        #                         url=f"{config.API_URL}/chat",
        #                         json={
        #                             "provider": st.session_state.provider,
        #                             "model_name": st.session_state.model_name,
        #                             "messages": st.session_state.messages,
        #                         },
        #                     )

    #    output = api_call("post", f"{config.API_URL}/chat", json={"provider": st.session_state.provider, "model_name": st.session_state.model_name, "messages": st.session_state.messages})
        success, response_data = api_call(
            "post",
            f"{config.API_URL}/chat",
            json={
                "provider": st.session_state.provider,
                "model_name": st.session_state.model_name,
                "messages": st.session_state.messages,
            },
            timeout=60,
        )

        if success and isinstance(response_data, dict) and "message" in response_data:
            answer = response_data["message"]
        else:
            # Fall back to an error message if the API call failed or the expected
            # "messages" field is not present in the response.
            if isinstance(response_data, dict):
                answer = response_data.get("message", "Failed to get response from API.")
            else:
                answer = "Failed to get response from API."

        # If API call was successful, extract assistant message from response data
        st.markdown(response_data["message"]) # Display assistant message in chat interface from API response

    # Add assistant response to session state i.e. chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})