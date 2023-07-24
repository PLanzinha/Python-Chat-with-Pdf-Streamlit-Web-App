import streamlit as st
from chains import load_pdf_retrieval_chain
from langchain.memory import StreamlitChatMessageHistory
from utils import save_chat_history_json, load_chat_history_json, get_timestamp
from pdf_handler import add_documents_to_db
import yaml
import os

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)


def load_chain(chat_history):
    return load_pdf_retrieval_chain(chat_history)


def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""


def set_send_input():
    st.session_state.send_input = True
    clear_input_field()


def track_index():
    st.session_state.session_index_tracker = st.session_state.session_key


def save_chat_history():
    if st.session_state.history:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp() + ".json"
            save_chat_history_json(st.session_state.history,
                                   os.path.join(config["chat_history_path"], st.session_state.new_session_key))
            # st.rerun()
        else:
            save_chat_history_json(st.session_state.history,
                                   os.path.join(config["chat_history_path"], st.session_state.session_key))


def main():
    st.title("Local Document Chat")
    chat_container = st.container()
    st.sidebar.title("Chat History")
    chat_session = ["new_session"] + os.listdir(config["chat_history_path"])

    if "send_input" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key is not None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

    index = chat_session.index(st.session_state.session_index_tracker)
    st.sidebar.selectbox("Select a Session", chat_session, key="session_key", index=index, on_change=track_index)

    if st.session_state.session_key != "new_session":
        st.session_state.history = load_chat_history_json(
            os.path.join(config["chat_history_path"], st.session_state.session_key))
    else:
        st.session_state.history = []

    with st.sidebar:
        st.sidebar.subheader("PDF Selection")

        uploaded_files = st.file_uploader("Select a folder", type="pdf", accept_multiple_files=True, key="pdf_upload")
        process_button = st.button("Load PDF")

        if process_button:
            with st.spinner("Loading"):
                if uploaded_files:
                    st.write('PDF loaded successfully')
                    add_documents_to_db(uploaded_files)
                else:
                    st.write('No PDF loaded')

    chat_history = StreamlitChatMessageHistory(key="history")
    llm_chain = load_chain(chat_history)

    user_input = st.text_input("Type here to ask documents", key="user_input", on_change=set_send_input)
    send_button = st.button("Send", key="send_button")

    if send_button or st.session_state.send_input:
        if st.session_state.user_question != "":
            with chat_container:
                llm_response = llm_chain.run(st.session_state.user_question)
                st.session_state.user_question = ""

    if chat_history.messages:
        with chat_container:
            for message in chat_history.messages:
                st.chat_message(message.type).write(message.content)

    save_chat_history()


if __name__ == "__main__":
    main()
