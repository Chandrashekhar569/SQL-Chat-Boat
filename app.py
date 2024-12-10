import streamlit as st 
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3 
from langchain_groq import ChatGroq

import os
from dotenv import load_dotenv
load_dotenv()

groq_api = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

local_db = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

redio_opt = ["Use SQLLite 3 Database-student.db", "Connect to MY SQL Database"]

selected_opt = st.sidebar.radio(label="Choose your db for Chat.", options=redio_opt)

if redio_opt.index(selected_opt)==1:
    db_uri = MYSQL
    mysql_host=st.sidebar.text_input("Enter your SQL Host Name.")
    mysql_user = st.sidebar.text_input("User Name")
    mysql_password = st.sidebar.text_input("Password",type="password")    
    mysql_db = st.sidebar.text_input("Enter your db name")
else:
    db_uri=local_db 


if not db_uri:
    st.info("please Enter Database info.")

############################
# If you want to work with OpenAI, uncomment this line

# import openai
# from langchain_openai import ChatOpenAI
# open_ai_api = os.getenv("OPENAI_API_KEY")
# llm = ChatOpenAI(openai_api_key=open_ai_api, model_name="gpt-4o",streaming=True)

##########################

llm = ChatGroq(groq_api_key=groq_api, model_name="Gemma2-9b-it",streaming=True)

# @st.cache_resource(ttl="2h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri==local_db:
        dbfilepath=(Path(__file__).parent/"student.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro",uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))

    
if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user, mysql_password, mysql_db)
else:
    db=configure_db(db_uri)


toolkit = SQLDatabaseToolkit(db=db,llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
)

if "messages" not in st.session_state or  st.sidebar.button("Clear message history"):
    st.session_state["messages"]=[{"role":"assistant", "content":"How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="Ask anything from Database.")


if user_query:
    st.session_state.messages.append({"role":"user","content":user_query})
    st.chat_message("user").write(user_query) 

    with st.chat_message("assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        response=agent.run(user_query,callbacks=[streamlit_callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)
