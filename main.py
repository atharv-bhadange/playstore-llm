import os, time
import streamlit as st
from dotenv import load_dotenv
from langchain_community.embeddings.huggingface import HuggingFaceInferenceAPIEmbeddings
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_community.llms import HuggingFaceEndpoint
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

embedding = HuggingFaceInferenceAPIEmbeddings(
        api_key = HF_TOKEN, model_name = "hkunlp/instructor-xl" #thenlper/gte-large # type: ignore
)


def get_vector_store(documents):

    vector_store = Qdrant.from_documents(documents, embedding, url="http://qdrantdb:6333/")

    return vector_store

def get_conversational_chain():

    prompt_template = """
    You are a game enthusiast and you are looking for a game to play. You have found a list of games and you want to know more about them. You have the following context:\n {context}?\n
    Provide a brief description of the game and its features. You can also provide a link to the game's page on the Google Play Store. You can also provide a list of tags that describe the game.\n
    Format the answer correctly as text and provide a link to the game's page on the Google Play Store.\n

    Context:\n {context}?\n
    History:\n {chat_history}\n
    Question: \n{question}\n

    Answer:
    """

    model = HuggingFaceEndpoint(
        repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.75,
        max_new_tokens=1024,
        # return_full_text=False,
        huggingfacehub_api_token = HF_TOKEN
    )

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "chat_history", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

def user_input(user_question, new_db, chain):

    if user_question is not None:
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)
            with st.spinner("Scanning Knowledge Base..."):
                docs = new_db.similarity_search(user_question)

                print("Found docs")
    
                response = chain(
                    {"input_documents":docs, "question": user_question, "chat_history": st.session_state.messages}
                    , return_only_outputs=True)
    

    def stream_data():
        for line in response["output_text"].split(" "):
            yield line + " "
            time.sleep(0.06)

    if st.session_state.messages[-1]["role"] != "assistant":
            # st.session_state.messages[-1]["content"] = user_question
        with st.chat_message("assistant"):
                st.write_stream(stream_data)
        new_ai_message = {"role": "assistant", "content": response["output_text"]}
        st.session_state.messages.append(new_ai_message)

def main():
    st.set_page_config(
            page_title="Game recommendation AI Assistant",
            layout="wide"
        )
    
    st.title("Game recommendation AI Assistant")
    st.write("This AI assistant can help you find the best games to play. Ask any question about the games listed below and the AI will provide you with the information you need.")

    # Load JSON data from file
    loader = JSONLoader(file_path="./game_data.json", jq_schema=".", text_content=False)
    documents = loader.load()
    

    print("loaded")
    vdb = get_vector_store(documents)
    print("vdb")
    chain = get_conversational_chain()
    print("chain done")

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! What type of game are you looking for?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


    user_prompt = st.chat_input()

    if user_prompt:
        user_input(user_prompt, vdb, chain)

if __name__ == "__main__":
    main()

