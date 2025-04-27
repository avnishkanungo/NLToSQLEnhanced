import logging
import os
import time
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions,
    SpeakWSOptions,
    SpeakWebSocketEvents
)

load_dotenv()

tts_app_socketio = Flask("tts_app_socketio")
tts_socketio = SocketIO(tts_app_socketio, cors_allowed_origins=['http://127.0.0.1:8000'])
last_time = 0
header_sent = False

API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

deepgram = DeepgramClient(API_KEY, config)

dg_tts_connection = None

def initialize_deepgram_tts_connection():

    global dg_tts_connection
    dg_tts_connection = deepgram.speak.websocket.v("1")
    
    def on_open(self, open, **kwargs):
        print(f"\n\n{open}\n\n")

    def on_flush(self, flushed, **kwargs):
        print(f"\n\n{flushed}\n\n")
        flushed_str = str(flushed)
        # tts_socketio.send(flushed_str)
        tts_socketio.emit("tts_audio_done")

    def on_binary_data(self, data, **kwargs):
        print("Received binary data")

        global last_time
        global header_sent
        if time.time() - last_time > 3:
        # if not header_sent:
            print("------------ [Binary Data] Attach header.\n")

            # Add a wav audio container header to the file if you want to play the audio
            # using the AudioContext or media player like VLC, Media Player, or Apple Music
            # Without this header in the Chrome browser case, the audio will not play.
            header = bytes(
                [
                    0x52,
                    0x49,
                    0x46,
                    0x46,  # "RIFF"
                    0x00,
                    0x00,
                    0x00,
                    0x00,  # Placeholder for file size
                    0x57,
                    0x41,
                    0x56,
                    0x45,  # "WAVE"
                    0x66,
                    0x6D,
                    0x74,
                    0x20,  # "fmt "
                    0x10,
                    0x00,
                    0x00,
                    0x00,  # Chunk size (16)
                    0x01,
                    0x00,  # Audio format (1 for PCM)
                    0x01,
                    0x00,  # Number of channels (1)
                    0x80,
                    0xBB,
                    0x00,
                    0x00,  # Sample rate (48000)
                    0x00,
                    0xEE,
                    0x02,
                    0x00,  # Byte rate (48000 * 2)
                    0x02,
                    0x00,  # Block align (2)
                    0x10,
                    0x00,  # Bits per sample (16)
                    0x64,
                    0x61,
                    0x74,
                    0x61,  # "data"
                    0x00,
                    0x00,
                    0x00,
                    0x00,  # Placeholder for data size
                ]
            )
            # tts_socketio.send(header)
            tts_socketio.emit("tts_audio_chunk", header)
            last_time = time.time()
            # header_sent = True
        # tts_socketio.send(data)
        
        tts_socketio.emit("tts_audio_chunk", data)
        # print("tts_audio_chunk", header+data)
        # tts_socketio.emit("test_event", "hello")

    def on_close(self, close, **kwargs):
        print(f"\n\n{close}\n\n")
        header_sent = False
        

    dg_tts_connection.on(SpeakWebSocketEvents.Open, on_open)
    dg_tts_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
    dg_tts_connection.on(SpeakWebSocketEvents.Flushed, on_flush)
    dg_tts_connection.on(SpeakWebSocketEvents.Close, on_close)

    options = SpeakWSOptions(
                    model="aura-asteria-en",
                    encoding="linear16",
                    sample_rate=48000,
                )
    
    if dg_tts_connection.start(options) is False: # THIS CAUSES ERROR
        print("Failed to start connection")
        exit()

@tts_socketio.on('play_query_result')
def handle_play_query_result(data):
    print("play_query_result", data)
    initialize_deepgram_tts_connection()
    if dg_tts_connection:
        dg_tts_connection.send(data.get("result"))
    else:
        print("Failed to start connection")
        exit()
    
    dg_tts_connection.flush()
    # tts_socketio.emit("tts_audio_chunk")
    # Add your audio playback logic here
    # For example, you can send the audio data to the client
    # or play it using the AudioContext

if __name__ == '__main__':
    logging.info("Starting TTS SocketIO server.")
    tts_socketio.run(tts_app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5002)