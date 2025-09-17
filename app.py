import streamlit as st
import asyncio
import json
import base64
from websockets.sync.client import connect
from streamlit_webrtc import webrtc_streamer, WebRtcStreamerContext
import av
import os
import threading
import queue
import time

# Set up the Streamlit page configuration
st.set_page_config(page_title="Streamlit Realtime Bot", page_icon="💬")
st.title("Realtime Interview Bot")

# --- Configuration ---
# You must set the OPENAI_API_KEY environment variable or uncomment the next line
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

WEBSOCKET_URL = "wss://api.openai.com/v1/realtime"
REALTIME_MODEL = "gpt-realtime"

# --- Session State Initialization ---
# This is the crucial fix: Initialize all session state variables at the start.
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'websocket_thread' not in st.session_state:
    st.session_state.websocket_thread = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
# Initialize the websocket_connection attribute to prevent the error
if 'websocket_connection' not in st.session_state:
    st.session_state.websocket_connection = None
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = queue.Queue()
if 'connection_ready' not in st.session_state:
    st.session_state.connection_ready = False

# --- WebSocket Thread Manager ---
def run_websocket(personal_info):
    try:
        ws = connect(
            WEBSOCKET_URL,
            extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        )
        st.session_state.websocket_connection = ws
        st.session_state.connection_ready = True

        # Initial message to configure the session with personal info and system prompt
        system_prompt = (
            f"You are an HR executive interviewing an interviewee named {personal_info['name']} "
            f"with experience: {personal_info['experience']} and skills: {personal_info['skills']}. "
            f"Interview them for the {personal_info['level']} {personal_info['position']} "
            f"at the company {personal_info['company']}."
        )
        
        initial_config = {
            "type": "session.begin",
            "model": REALTIME_MODEL,
            "system_prompt": system_prompt,
            "audio_format": "pcm_16khz_16bit_mono"
        }
        ws.send(json.dumps(initial_config))

        # Initial message from the "interviewer"
        hello_message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": "Hello, my name is Interviewer. Can you please introduce yourself?",
            },
        }
        ws.send(json.dumps(hello_message))

        while ws.connected:
            message = ws.recv()
            data = json.loads(message)
            st.session_state.message_queue.put(data)

    except Exception as e:
        print(f"WebSocket thread error: {e}")
        st.session_state.connection_ready = False
    finally:
        if 'websocket_connection' in st.session_state and st.session_state.websocket_connection:
            st.session_state.websocket_connection.close()
            st.session_state.websocket_connection = None
        st.session_state.connection_ready = False

# --- Audio Processor Class for streamlit-webrtc ---
class AudioProcessor:
    def __init__(self):
        pass

    def recv(self, frame: av.AudioFrame):
        # Check if WebSocket connection is ready and available
        if (hasattr(st.session_state, 'websocket_connection') and 
            st.session_state.websocket_connection and 
            st.session_state.websocket_connection.connected):
            
            audio_data = frame.to_ndarray(format="s16le")
            audio_message = {
                "type": "audio.input.delta",
                "delta": base64.b64encode(audio_data.tobytes()).decode("utf-8")
            }
            try:
                st.session_state.websocket_connection.send(json.dumps(audio_message))
            except Exception as e:
                print(f"Error sending audio: {e}")
        return None

# --- Streamlit UI and Logic ---

# Setup Phase
if not st.session_state.setup_complete:
    st.subheader('Personal Information')
    st.session_state["name"] = st.text_input("Name", value=st.session_state.get("name", ""))
    st.session_state["experience"] = st.text_area("Experience", value=st.session_state.get("experience", ""))
    st.session_state["skills"] = st.text_area("Skills", value=st.session_state.get("skills", ""))
    st.session_state["company"] = st.text_input("Company Name", value=st.session_state.get("company", ""))
    st.session_state["position"] = st.text_input("Position Title", value=st.session_state.get("position", ""))
    st.session_state["level"] = st.text_input("Level", value=st.session_state.get("level", ""))
    st.session_state["job_post"] = st.text_area("Job Post Description (Optional)", value=st.session_state.get("job_post", ""))
    
    if st.button("Start Realtime Interview"):
        st.session_state.setup_complete = True
        st.rerun()

# Interview Phase
else:
    st.subheader("Realtime Conversation")
    
    # Initialize a WebSocket connection in a separate thread if not already running
    if st.session_state.websocket_thread is None:
        personal_info = {
            'name': st.session_state['name'],
            'experience': st.session_state['experience'],
            'skills': st.session_state['skills'],
            'company': st.session_state['company'],
            'position': st.session_state['position'],
            'level': st.session_state['level']
        }
        # Start the WebSocket in a new thread
        st.session_state.websocket_thread = threading.Thread(
            target=run_websocket, args=(personal_info,), daemon=True
        )
        st.session_state.websocket_thread.start()
        st.session_state.is_listening = True

    # Wait for connection to be ready before starting WebRTC
    if st.session_state.connection_ready:
        # Use streamlit-webrtc for continuous audio streaming
        webrtc_ctx = webrtc_streamer(
            key="realtime-audio",
            audio_receiver_size=256,
            media_stream_constraints={"audio": True, "video": False},
            sendback_audio=False,
            # Remove the WebSocket connection parameter from the factory
            audio_processor_factory=lambda: AudioProcessor()
        )
        
        if st.session_state.is_listening:
            st.info("The interview is live. Start talking!")
    else:
        st.info("Connecting to the interview service... Please wait.")
        time.sleep(0.1)  # Small delay to prevent rapid rerunning
        st.rerun()
        
    # Process messages from the WebSocket thread
    while not st.session_state.message_queue.empty():
        message = st.session_state.message_queue.get()
        if message["type"] == "text.delta":
            if not st.session_state.conversation_history or st.session_state.conversation_history[-1].get("role") != message.get("role"):
                st.session_state.conversation_history.append({"role": message.get("role", "unknown"), "content": ""})
            st.session_state.conversation_history[-1]["content"] += message["delta"]
        elif message["type"] == "audio.delta":
            # This part is a placeholder. Streaming audio playback is not simple.
            st.audio(base64.b64decode(message["delta"]), format="audio/wav")

    # Display conversation history
    for message in st.session_state.conversation_history:
        st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")

    if st.button("End Interview"):
        # Stop the WebSocket thread and close the connection
        if st.session_state.websocket_connection:
            st.session_state.websocket_connection.close()
        if st.session_state.websocket_thread:
            st.session_state.websocket_thread.join()
        st.session_state.is_listening = False
        st.session_state.setup_complete = False
        st.session_state.websocket_thread = None
        st.session_state.connection_ready = False
        st.rerun()
