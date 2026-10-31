import streamlit as st
from chatbot_ui.core.config import config
import requests 

def api_call(method,url,**kwargs):

    def _show_error_popup(message):
        """"show error message as a popup in the top right corner of the screen"""
        st.session_state['error_popuup'] = {
            "message": message,
            "visible": True
        }

    try:
        response = getattr(requests, method)(url,**kwargs)

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            response_data = {'message': 'Invalid response format from server'}

        if response.ok:
            return True, response_data

        return False, response_data

    except requests.exceptions.ConnectionError:
        _show_error_popup("Connection error. Please check your internet connection.")
        return False, {'message': 'Connection error'}
    except requests.exceptions.Timeout:
        _show_error_popup("Request timed out. Please try again later.")
        return False, {'message': 'Request timed out'}
    except Exception as e:
        _show_error_popup(f"An unexpected error occurred: {str(e)}")
        return False, {'message': f'An unexpected error occurred: {str(e)}'}

with st.sidebar:
    provider = st.selectbox("Select LLM Provider", ["OpenAI", "Anthropic"])
    if provider == "OpenAI":
        model_name = st.selectbox("Select OpenAI Model", ["gpt-5-nano", "gpt-5-mini"])
    elif provider == "Anthropic":
        model_name = st.selectbox("Select Anthropic Model", ["claude-sonnet-5-5", "claude-haiku-4-5-20251001"])

    st.session_state['provider'] = provider
    st.session_state['model_name'] = model_name # type: ignore

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': 'Leave me alone'}]

# Normalize conversations created before assistant messages used API-supported roles.
for message in st.session_state.messages:
    if message["role"] == "poet":
        message["role"] = "assistant"

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Write a poem about..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("poet"):
        output = api_call("post", f"{config.API_URL}/llm", json={
            "provider": st.session_state.provider,
            "model_name": st.session_state.model_name,
            "messages": st.session_state.messages
        })
        response_data =output[1]
        answer = response_data['message']
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer}) # type: ignore
