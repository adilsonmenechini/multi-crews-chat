
import streamlit as st
import requests
import os

# Use o nome do serviço Docker como hostname
# ou 'localhost' se estiver executando localmente
MANAGER_URL = os.getenv("MANAGER_URL", "http://localhost:8000")

st.title("🤖 Chat com Multi-Crews")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Qual a sua pergunta?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            r = requests.post(f"{MANAGER_URL}/chat", json={"text": prompt}, timeout=120)
            r.raise_for_status()
            response_data = r.json()
            full_response = response_data.get("reply", "Não obtive uma resposta clara.")
        except requests.exceptions.RequestException as e:
            full_response = f"Erro ao contatar o manager: {e}"
        
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
