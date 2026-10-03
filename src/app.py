import streamlit as st
from openai import OpenAI
from anthropic import Anthropic
from core.config import config

def run_llm(provider,model_name,messages,max_tokens=1000):
    if provider == "OpenAI":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content
    elif provider == "Anthropic":
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            messages=messages
        )
        return "".join(block.text for block in response.content if block.type == "text")
    else:
        raise ValueError("Unsupported provider")


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
        output = run_llm(st.session_state['provider'], st.session_state['model_name'], st.session_state.messages)
        response_data =output
        answer = response_data
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer}) # type: ignore
