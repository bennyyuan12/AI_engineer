import streamlit as st
from chatbot_ui.api_client import APIError, request_answer
from chatbot_ui.core.config import config

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': 'Ask me for book recommendations.'}]

# Normalize conversations created before assistant messages used API-supported roles.
for message in st.session_state.messages:
    if message["role"] == "poet":
        message["role"] = "assistant"

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about books..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Finding books..."):
                answer = request_answer(prompt, config.API_BASE_URL)
        except APIError as exc:
            st.error(str(exc))
        else:
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
