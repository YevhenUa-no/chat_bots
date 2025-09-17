import streamlit as st
import asyncio
import json
import base64
from websockets.sync.client import connect
from streamlit_webrtc import webrtc_streamer, WebRtcStreamerContext
import av
import os

# Set up the Streamlit page configuration
st.set_page_config(page_title="Streamlit Realtime Bot", page_icon="💬")
st.title("Realtime Interview Bot")

# --- Session State Management ---
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
if "websocket_connection" not in st.session_state:
    st.session_state.websocket_connection = None

# --- Configuration ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # You must set this environment variable
# If you don't use environment variable, uncomment this line:
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Note: The Realtime API endpoint and model are specific to OpenAI's new API.
# This URL and model name are examples and may need to be updated.
WEBSOCKET_URL = "wss://api.openai.com/v1/realtime"
REALTIME_MODEL = "gpt-realtime"

# --- Audio Processor Class for streamlit-webrtc ---
class AudioProcessor:
    def __init__(self, ws_connection, messages_queue):
        self.ws_connection = ws_connection
        self.messages_queue = messages_queue
        self.is_connected = False

    def recv(self, frame: av.AudioFrame):
        if not self.is_connected:
            return

        # Convert audio frame to raw PCM data
        audio_data = frame.to_ndarray(format="s16le")

        # Create a WebSocket message
        audio_message = {
            "type": "audio.input.delta",
            "delta": audio_data.tobytes()
        }

        # Send the audio data to the WebSocket
        try:
            self.ws_connection.send(json.dumps(audio_message))
        except Exception as e:
            st.error(f"Error sending audio: {e}")
            self.is_connected = False
            return None

        # Process any incoming messages from the WebSocket
        try:
            message = self.ws_connection.recv(timeout=0.01) # Use a small timeout
            # The message queue is a simple way to pass data from this thread to the main app loop
            self.messages_queue.put(message)
        except:
            pass # No new message, continue

        return None # Return None as we don't display audio frame

# --- Core WebSocket Connection and Message Handling Function ---
def manage_websocket_connection(personal_info):
    try:
        # Establish WebSocket connection
        ws = connect(
            WEBSOCKET_URL,
            extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        )
        st.session_state.websocket_connection = ws
        st.session_state.is_listening = True

        # Initial message to configure the session with personal info and system prompt
        system_prompt = (
            f"You are an HR executive interviewing an interviewee named {personal_info['name']} "
            f"with experience: {personal_info['experience']} and skills: {personal_info['skills']}. "
            f"Interview them for the {personal_info['level']} {personal_info['position']} "
            f"at {personal_info['company']}."
        )

        initial_config = {
            "type": "session.begin",
            "model": REALTIME_MODEL,
            "system_prompt": system_prompt,
            "audio_format": "pcm_16khz_16bit_mono"
        }
        ws.send(json.dumps(initial_config))

        st.success("Connected to Realtime API. You can start speaking now!")
        
        # Start the "interviewer" by sending a message
        hello_message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": "Hello, my name is Interviewer. Can you please introduce yourself?",
            },
        }
        ws.send(json.dumps(hello_message))


        # Asynchronously read responses from the WebSocket
        while st.session_state.is_listening:
            try:
                message = ws.recv()
                # Parse the JSON message
                data = json.loads(message)
                
                # Check for an audio response
                if data["type"] == "audio.delta":
                    audio_data_base64 = data["delta"]
                    audio_bytes = base64.b64decode(audio_data_base64)
                    
                    # You would need a custom component or method to play this audio
                    # as it streams in, not just as a full file.
                    # For a simple demo, you can save and play it.
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
                
                # Check for a text transcription
                if data["type"] == "text.delta":
                    text_delta = data["delta"]
                    st.session_state.conversation_history[-1]['content'] += text_delta
                    st.experimental_rerun()
            except Exception as e:
                # Handle cases where the connection is closed or timed out
                if not st.session_state.is_listening:
                    break
                st.error(f"WebSocket error: {e}")
                break
        
    except Exception as e:
        st.error(f"Failed to connect to WebSocket: {e}")
        st.session_state.is_listening = False
    finally:
        if st.session_state.websocket_connection:
            st.session_state.websocket_connection.close()

# --- Streamlit UI and Logic ---

if not st.session_state.setup_complete:
    # Existing setup code with text inputs
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
        st.session_state.conversation_history = []
        st.experimental_rerun()

else:
    # The actual interview
    st.subheader("Realtime Conversation")
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")

    # Use streamlit-webrtc for continuous audio streaming
    webrtc_ctx = webrtc_streamer(
        key="realtime-audio",
        audio_receiver_size=256,
        media_stream_constraints={"audio": True, "video": False},
        sendback_audio=False,
    )

    if webrtc_ctx.audio_receiver and not st.session_state.is_listening:
        # Start the WebSocket connection in a separate thread/task
        # This is a simplified call; you would need proper threading or async handling
        # For a full implementation, consider using a separate process or a robust library
        manage_websocket_connection({
            'name': st.session_state['name'],
            'experience': st.session_state['experience'],
            'skills': st.session_state['skills'],
            'company': st.session_state['company'],
            'position': st.session_state['position'],
            'level': st.session_state['level']
        })
    elif webrtc_ctx.audio_receiver and st.session_state.is_listening:
        st.info("The interview is live. Start talking!")
    
    if st.button("End Interview"):
        if st.session_state.websocket_connection:
            st.session_state.websocket_connection.close()
        st.session_state.is_listening = False
        st.session_state.setup_complete = False
        st.experimental_rerun()
