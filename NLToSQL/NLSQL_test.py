from NLToSQL import initialize_chain
import os
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
# Load environment variables
load_dotenv()

# Get the API key from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")


history = ChatMessageHistory()

# Initialize the chain
chain = initialize_chain(
    db_user="root",
    db_password="",
    db_host="localhost",
    db_name="classicmodels",
    API_KEY=API_KEY
)

# Test the chain with a dictionary input
result = chain.invoke({"question": "What are the 10 most expensive products?", "messages": history.messages})

print("Result:", result)
