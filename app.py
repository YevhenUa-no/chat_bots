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
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'websocket_manager' not in st.session_state:
    st.session_state.websocket_manager = None

# --- WebSocket Manager Class ---
class WebSocketManager:
    def __init__(self):
        self.websocket = None
        self.message_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.connection_ready = threading.Event()
        self.stop_event = threading.Event()
        
    def start_connection(self, personal_info):
        self.thread = threading.Thread(
            target=self._run_websocket, 
            args=(personal_info,), 
            daemon=True
        )
        self.thread.start()
        
    def _run_websocket(self, personal_info):
        try:
            ws = connect(
                WEBSOCKET_URL,
                extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            self.websocket = ws
            self.connection_ready.set()

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

            # Handle both WebSocket messages and audio queue
            while ws.connected and not self.stop_event.is_set():
                try:
                    # Check for audio data to send
                    try:
                        audio_message = self.audio_queue.get_nowait()
                        ws.send(json.dumps(audio_message))
                    except queue.Empty:
                        pass
                    
                    # Check for WebSocket messages (with timeout to allow audio processing)
                    ws.settimeout(0.1)  # 100ms timeout
                    try:
                        message = ws.recv()
                        data = json.loads(message)
                        self.message_queue.put(data)
                    except TimeoutError:
                        continue  # Continue to check audio queue
                        
                except Exception as e:
                    if not self.stop_event.is_set():
                        print(f"WebSocket loop error: {e}")
                    break

        except Exception as e:
            print(f"WebSocket thread error: {e}")
        finally:
            self.connection_ready.clear()
            if self.websocket:
                try:
                    self.websocket.close()
                except:
                    pass
                self.websocket = None
    
    def send_audio(self, audio_data):
        if self.connection_ready.is_set():
            audio_message = {
                "type": "audio.input.delta",
                "delta": base64.b64encode(audio_data).decode("utf-8")
            }
            try:
                self.audio_queue.put_nowait(audio_message)
            except queue.Full:
                print("Audio queue full, dropping frame")
    
    def get_messages(self):
        messages = []
        try:
            while True:
                message = self.message_queue.get_nowait()
                messages.append(message)
        except queue.Empty:
            pass
        return messages
    
    def is_connected(self):
        return self.connection_ready.is_set()
    
    def stop(self):
        self.stop_event.set()
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2)

# --- Audio Processor Class for streamlit-webrtc ---
class AudioProcessor:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager

    def recv(self, frame: av.AudioFrame):
        if self.websocket_manager and self.websocket_manager.is_connected():
            try:
                audio_data = frame.to_ndarray(format="s16le")
                self.websocket_manager.send_audio(audio_data.tobytes())
            except Exception as e:
                print(f"Error processing audio: {e}")
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
    
    # Initialize WebSocket manager if not already running
    if st.session_state.websocket_manager is None:
        st.session_state.websocket_manager = WebSocketManager()
        personal_info = {
            'name': st.session_state['name'],
            'experience': st.session_state['experience'],
            'skills': st.session_state['skills'],
            'company': st.session_state['company'],
            'position': st.session_state['position'],
            'level': st.session_state['level']
        }
        st.session_state.websocket_manager.start_connection(personal_info)
        st.session_state.is_listening = True

    # Check connection status
    if st.session_state.websocket_manager.is_connected():
        # Use streamlit-webrtc for continuous audio streaming
        webrtc_ctx = webrtc_streamer(
            key="realtime-audio",
            audio_receiver_size=256,
            media_stream_constraints={"audio": True, "video": False},
            sendback_audio=False,
            audio_processor_factory=lambda: AudioProcessor(st.session_state.websocket_manager)
        )
        
        if st.session_state.is_listening:
            st.info("The interview is live. Start talking!")
    else:
        st.info("Connecting to the interview service... Please wait.")
        time.sleep(0.5)  # Wait a bit before checking again
        st.rerun()
        
    # Process messages from the WebSocket manager
    if st.session_state.websocket_manager:
        messages = st.session_state.websocket_manager.get_messages()
        for message in messages:
            if message.get("type") == "response.text.delta":
                # Handle text responses
                if not st.session_state.conversation_history or st.session_state.conversation_history[-1].get("role") != "assistant":
                    st.session_state.conversation_history.append({"role": "assistant", "content": ""})
                st.session_state.conversation_history[-1]["content"] += message.get("delta", "")
            elif message.get("type") == "input_audio_buffer.speech_started":
                # User started speaking
                if not st.session_state.conversation_history or st.session_state.conversation_history[-1].get("role") != "user":
                    st.session_state.conversation_history.append({"role": "user", "content": "[Speaking...]"})
            elif message.get("type") == "conversation.item.input_audio_transcription.completed":
                # User speech transcription completed
                if st.session_state.conversation_history and st.session_state.conversation_history[-1].get("role") == "user":
                    st.session_state.conversation_history[-1]["content"] = message.get("transcript", "")
            elif message.get("type") == "response.audio.delta":
                # Handle audio responses - placeholder for now
                pass

    # Display conversation history
    for message in st.session_state.conversation_history:
        st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")

    if st.button("End Interview"):
        # Stop the WebSocket manager
        if st.session_state.websocket_manager:
            st.session_state.websocket_manager.stop()
        
        # Reset session state
        st.session_state.is_listening = False
        st.session_state.setup_complete = False
        st.session_state.websocket_manager = None
        st.session_state.conversation_history = []
        st.rerun()
