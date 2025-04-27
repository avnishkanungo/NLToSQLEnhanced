import logging
import os
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions
)
from NLToSQL.NLToSQL import initialize_chain
from langchain_community.chat_message_histories import ChatMessageHistory
load_dotenv()

app_socketio = Flask("app_socketio")
socketio = SocketIO(app_socketio, cors_allowed_origins=['http://127.0.0.1:8000', 'http://localhost:8000'])
history = ChatMessageHistory()

API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

deepgram = DeepgramClient(API_KEY, config)


dg_connection = None

def initialize_deepgram_connection():
    global dg_connection
    # Initialize Deepgram client and connection
    dg_connection = deepgram.listen.live.v("1")

    def on_open(self, open, **kwargs):
        print(f"\n\n{open}\n\n")

    def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            print(result.channel.alternatives[0].transcript)
            socketio.emit('transcription_update', {'transcription': transcript})

    def on_close(self, close, **kwargs):
        print(f"\n\n{close}\n\n")

    def on_error(self, error, **kwargs):
        print(f"\n\n{error}\n\n")

    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    # Define the options for the live transcription
    options = LiveOptions(model="nova-3", 
                          language="multi", 
                          endpointing=10000)

    if dg_connection.start(options) is False: # THIS CAUSES ERROR
        print("Failed to start connection")
        exit()
    

@socketio.on('audio_stream')
def handle_audio_stream(data):
    if dg_connection:
        dg_connection.send(data)

@socketio.on('toggle_transcription')
def handle_toggle_transcription(data):
    print("toggle_transcription", data)
    action = data.get("action")
    if action == "start":
        print("Starting Deepgram connection")
        initialize_deepgram_connection()

@socketio.on('run_query')
def run_query(data):
    print("run_query", data)
    question = data.get("question")
    result = chain.invoke({"question": question, "messages": history.messages})
    history.add_user_message(question)
    history.add_ai_message(result)
    socketio.emit('query_result', {'result': result})

@socketio.on('connect')
def server_connect():
    print('Client connected')

@socketio.on('restart_deepgram')
def restart_deepgram():
    print('Restarting Deepgram connection')
    initialize_deepgram_connection()

if __name__ == '__main__':
    logging.info("Connecting to database")
    chain = initialize_chain(db_user="root", db_password="", db_host="localhost", db_name="classicmodels",API_KEY=OPENAI_API_KEY)
    logging.info("Starting SocketIO server.")
    socketio.run(app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5001)
