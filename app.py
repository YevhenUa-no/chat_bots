import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from streamlit_mic_recorder import mic_recorder # Import the mic_recorder component
import io # To handle audio bytes
import os # For temporary file creation (optional, but good practice)
from pydub import AudioSegment # For audio format conversion

# Setting up the Streamlit page configuration
st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="💬")
st.title("Chatbot")

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
# --- NEW: Microphone recorder session state variables ---
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
# --- END NEW ---

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# --- NEW: Function to transcribe audio using OpenAI Whisper ---
# This decorator was causing the error: @st.cache_data(show_spinner=False)
# It has been removed because OpenAI client objects are not serializable by Streamlit's cache.
def get_openai_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def transcribe_audio(audio_bytes):
    if audio_bytes is None:
        return ""

    client = get_openai_client()

    # Convert audio bytes to a format Whisper can accept (e.g., MP3 or WAV)
    # The mic_recorder typically returns WAV bytes, but converting to MP3 can be more robust for Whisper
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        # Export to a temporary MP3 file or use BytesIO with named parameters
        # For direct API call, BytesIO is often preferred
        mp3_audio_stream = io.BytesIO()
        audio_segment.export(mp3_audio_stream, format="mp3")
        mp3_audio_stream.name = "audio.mp3" # Whisper API needs a filename

        with st.spinner("Transcribing audio..."):
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=mp3_audio_stream,
                response_format="text"
            )
        return transcript
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return ""
# --- END NEW ---


# Setup stage for collecting user details
if not st.session_state.setup_complete:
    st.subheader('Personal Information')

    # Initialize session state for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""


    # Get personal information input
    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40)
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200)
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200)


    # Company and Position Section
    st.subheader('Company and Position')

    # Initialize session state for company and position information and setting default values
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"])
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"])
    )


    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# Interview phase
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
    """
    Start by introducing yourself
    """,
    icon="👋",
    )

    # Setting OpenAI model if not already initialized
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    # Initializing the system prompt for the chatbot
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                        f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                        f"at the company {st.session_state['company']}")
        }]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # --- Microphone recording and Whisper integration ---
    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        # Text input for chat
        prompt = st.chat_input("Your response", max_chars=1000, key="chat_text_input")

    with col2:
        # Microphone recorder button
        st.session_state.audio_bytes = mic_recorder(
            start_prompt="🎙️ Speak",
            stop_prompt="⏹️ Stop",
            just_once=True, # Transcribe once per recording
            use_container_width=True,
            key="mic_recorder_button"
        )
    # --- END NEW ---

    # --- Process audio if recorded ---
    if st.session_state.audio_bytes:
        # Transcribe the audio using Whisper
        voice_transcript = transcribe_audio(st.session_state.audio_bytes['bytes'])
        if voice_transcript:
            prompt = voice_transcript # Set the prompt from the voice transcript
            st.session_state.audio_bytes = None # Clear audio bytes after use
            st.rerun() # Rerun to process the new prompt immediately

    # Handle user input (either typed or from Whisper)
    if st.session_state.user_message_count < 5:
        if prompt: # If there's a prompt (either typed or from Whisper)
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            # Clear the prompt from the chat_input widget after it's been used
            # This is important to prevent re-adding the same message on reruns
            st.session_state.chat_text_input = "" # This will reset the text input

            # Get assistant response if user message count allows
            if st.session_state.user_message_count < 4:
                client = get_openai_client() # Get client
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Increment the user message count
            st.session_state.user_message_count += 1
            st.rerun() # Rerun to display the new messages and potentially update chat_complete
        else:
            # If no prompt, but audio was just processed and transcript set, we already rerun above.
            # This 'else' block ensures typed input still works if voice_transcript is empty
            pass


    # Check if the user message count reaches 5
    if st.session_state.user_message_count >= 5 and not st.session_state.chat_complete:
        st.session_state.chat_complete = True
        st.rerun() # Rerun to transition to feedback stage

# Show "Get Feedback"
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")
        st.rerun() # Rerun to display feedback

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = get_openai_client() # Get client for feedback

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        # This will clear all session state variables and force a full reload
        for key in st.session_state.keys():
            del st.session_state[key]
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
