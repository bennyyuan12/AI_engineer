import requests
import streamlit as st

from chatbot_ui.core.config import config


st.title("Chatbot")

with st.sidebar:
    provider = st.selectbox("Select LLM Provider", ["OpenAI", "Anthropic"])
    if provider == "OpenAI":
        model_name = st.selectbox("Select OpenAI Model", ["gpt-5-nano", "gpt-5-mini"])
    else:
        model_name = st.selectbox(
            "Select Anthropic Model", ["claude-sonnet-5-5", "claude-haiku-4-5-20251001"]
        )

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Write a poem about..."):
    messages = st.session_state.messages + [{"role": "user", "content": prompt}]
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{config.API_BASE_URL.rstrip('/')}/chat",
                    json={
                        "provider": provider,
                        "model_name": model_name,
                        "messages": messages,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                answer = response.json()["message"]
        except (requests.RequestException, ValueError, KeyError):
            st.error("Could not get a response from the API. Please try again.")
        else:
            st.markdown(answer)
            st.session_state.messages = messages + [
                {"role": "assistant", "content": answer}
            ]
