import streamlit as st
from agente import responder

st.set_page_config(page_title="Murilo Antonio da GFK", layout="wide")

st.title("🤖 Murilo Antonio da GFK")
st.write("Faça perguntas sobre vendas, preço, market share e mais")

pergunta = st.text_input("Digite sua pergunta:")

if pergunta:
    resposta = responder(pergunta)
    st.text_area("Resposta:", resposta, height=400)