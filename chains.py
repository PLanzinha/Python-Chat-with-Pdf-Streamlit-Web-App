from prompt_templates import memory_prompt_template
from langchain.chains import LLMChain
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms import CTransformers
from langchain_community.vectorstores import Chroma
import chromadb
import yaml


def get_llm_model():
    return create_llm()


def get_embeddings():
    return create_embeddings()


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)


def create_llm(model_path=config["model_path"]["large"], model_type=config["model_type"],
               model_config=config["model_config"]):
    llm = CTransformers(model=model_path, model_type=model_type, config=model_config)
    return llm


def create_embeddings(embeddings_path=config["embeddings_path"]):
    return HuggingFaceInstructEmbeddings(model_name=embeddings_path)


def create_chat_memory(chat_history):
    return ConversationBufferMemory(memory_key="history", chat_memory=chat_history, k=3)


def create_prompt_from_template(template):
    return PromptTemplate.from_template(template)


def create_llm_chain(llm, chat_prompt, memory):
    return LLMChain(llm=llm, prompt=chat_prompt, memory=memory)


def load_normal_chain(chat_history):
    return chatChain(chat_history)


def load_vector(embeddings):
    persistent_client = chromadb.PersistentClient("vector_db")
    langchain_chroma = Chroma(
        client=persistent_client,
        collection_name="pdf",
        embedding_function=embeddings,
    )
    return langchain_chroma


def load_pdf_retrieval_chain(chat_history):
    return pdfChatChain(chat_history)


def load_retrieval_qa_chain(llm, memory, vector_db):
    return RetrievalQA.from_llm(llm=llm, memory=memory, retriever=vector_db.as_retriever())


class pdfChatChain:
    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        self.vector_db = load_vector(get_embeddings())
        self.llm_chain = None

    def run(self, user_input):
        if self.llm_chain is None:
            llm = get_llm_model()
            self.llm_chain = load_retrieval_qa_chain(llm, self.memory, self.vector_db)
        return self.llm_chain.invoke(input=user_input, history=self.memory.chat_memory.messages, stop=["Human:"])


class chatChain:
    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        self.llm_chain = None

    def run(self, user_input):
        if self.llm_chain is None:
            llm = get_llm_model()
            chat_prompt = create_prompt_from_template(memory_prompt_template)
            self.llm_chain = create_llm_chain(llm, chat_prompt, self.memory)
        return self.llm_chain.invoke(input=user_input, history=self.memory.chat_memory.messages, stop=["Human:"])
