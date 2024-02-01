import os
import json
import re
from dotenv import load_dotenv, find_dotenv
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents.agent_toolkits import GmailToolkit
from bs4 import BeautifulSoup
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import(
    HumanMessage,
    SystemMessage
)
from gmail_agent import gmail_agent
import streamlit as st

def auto_mail():
    st.title(':blue[Auto Mail Responder]')
    st.write("Auto Mail Responder Started..")
    _ = load_dotenv(find_dotenv())
    os.environ['OPENAI_API_KEY'] = os.environ["OPENAI_API_KEY"]

    embedding = OpenAIEmbeddings()
    persist_directory = 'vector_store/chroma/'

    # Load the vector store
    st.write("Loading the Vector Store..")
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k":2})

    llm = OpenAI(temperature=0)
    toolkit = GmailToolkit() 

    st.write("Initializing Agent..")
    agent = initialize_agent(
        tools=toolkit.get_tools(),
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    )

    # emails = gmail_agent.getEmails()
    # print(f"No. of mails: {len(emails)}")


    # Specify the number of emails to fetch
    n = 2  
    st.write("Fetching Emails...")
    emails = gmail_agent.fetch_last_n_emails(n)
    st.write(json.dumps(emails, indent=2))
    # print(json.dumps(emails, indent=2))


    for i in range(len(emails)):
    #     print(emails[i]['body'])
        html_body = emails[i]['body']
        try:
            soup = BeautifulSoup(str(html_body), 'html.parser')
            # Extract the text from the parsed HTML
            text = soup.get_text()
            # Print the extracted text
    #         print(text)
            text = re.sub(r'[\[\]\r\n]', '', text)
            emails[i]['body'] = text
        except Exception as e:
            # Print an error message if there was an error parsing the HTML
            print(f"Error parsing HTML: {str(e)}")

    print(emails)

    for i in range(len(emails)):
        question = emails[i]['body']
        docs = retriever.get_relevant_documents(query=question)
        best_retrieve = docs[0].page_content
        customer_name = emails[i]['sender']
        subject = emails[i]['subject']
        chat_messages = [
            SystemMessage(content='You are an expert assistant with expertise in reading user manuals of products'),
            HumanMessage(content=f'Please provide an answer to the following question {question} to {customer_name} from the:\n TEXT: {best_retrieve} in a professional email tone using greetings from XYZ Company')
                        ]
        
        llm=ChatOpenAI(model_name='gpt-3.5-turbo')
        query_response = llm(chat_messages).content
        query_response = query_response.replace("\n","<br>")
        print(query_response)
        agent.run(f"Send a gmail reply to {customer_name} for {subject} with response {query_response}")
        st.write("Responded to mails..")

if st.button("Run Code"):
    auto_mail()