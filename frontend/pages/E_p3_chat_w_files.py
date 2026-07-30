## E_p3_chat_w_files.py
# imports
#
# from pathlib import Path
import openai  # import OpenAI
import streamlit as st

# from streamlit_chat import chat
"""
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template

"""


def get_vectorstore(text_chunks):
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

    return vector_store


def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
    )


def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        response = st.session_state.conversation({"question": user_question})
        st.session_state.chat_history = response["chat_history"]
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(
                    user_template.replace("{{MSG}}", message.content),
                    unsafe_allow_html=True,
                )
            else:
                st.write(
                    bot_template.replace("{{MSG}}", message.content),
                    unsafe_allow_html=True,
                )
    else:
        st.write("Please upload PDFs and click process")


"""
"""


"""
@st.cache(allow_output_mutation=True)
def get_chat():
    return chat()


chat = get_chat()
chat.add_message("Hallo, wie kann ich Ihnen heute helfen?", "bot")

"""


def get_openai_response(user_input):
    """
    This function sends the user input to OpenAI's Chat API and returns the model's response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Specify the model for chat applications
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ],
        )
        # Extracting the text from the last response in the chat
        return (
            response.choices[0].message["content"].strip()
            if response.choices
            else "No response from the model."
        )

    except Exception as e:
        return f"An error occurred: {str(e)}"


"""
Step 3: Testing and Iteration

After integrating OpenAI, it's crucial to test your chatbot extensively.
Experiment with different types of queries to see how well the chatbot
responds. You may adjust the parameters in the ChatCompletion.create method
to fine-tune the responses according to your needs.
"""


def chatbot_response(prompt):
    # Hier könnte eine einfache Logik oder eine KI-API-Abfrage stehen
    # response = openai.Completion.create(
    #     engine="text-davinci-003",
    #    prompt=prompt,
    #    max_tokens=100
    # )
    # return response.choices.text.strip()
    return f"Das ist eine generische Antwort auf: {prompt}"


def show():
    st.header("🏠 Startseite ")
    st.subheader("**🤖 File Chat**")

    # st.set_page_config(page_title="Chat with multiple files",
    #                    page_icon=":books:")
    # st.write(css, unsafe_allow_html=True)

    # Set OpenAI API key from Streamlit secrets
    # client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"  # 3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Zeige den Chatverlauf an
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Eingabefeld für den Benutzer
    if prompt := st.chat_input("Frage mich etwas!"):
        # Füge die Benutzerfrage zum Chatverlauf hinzu
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Hier würde die Antwort des Chatbots generiert werden
        response = chatbot_response(prompt)
        #  response = f"Das ist eine Antwort auf: '{prompt}'"

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
