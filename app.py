import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

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
# --- NEW: Voice input related session state variables ---
if "voice_input_active" not in st.session_state:
    st.session_state.voice_input_active = False
if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""
if "start_recording" not in st.session_state:
    st.session_state.start_recording = False
# --- END NEW ---


# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# --- NEW: JavaScript for voice input ---
# This script directly uses webkitSpeechRecognition and updates Streamlit's session state
# via `streamlit.set()`.
voice_script = """
async function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window)) {
    alert('Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
    return null;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.continuous = false; // Set to true for continuous recognition
  recognition.interimResults = false; // Set to true for interim results
  recognition.lang = 'en-US'; // Set the language for recognition

  return new Promise((resolve, reject) => {
    recognition.onresult = (event) => {
      // Get the final transcript from the results
      const transcript = event.results[0][0].transcript;
      resolve(transcript);
      // Update Streamlit's session state with the transcript and set active to false
      streamlit.set({voice_input_active: false, voice_transcript: transcript});
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      reject(event.error);
      // On error, ensure voice input is no longer active
      streamlit.set({voice_input_active: false});
      // Optionally show a message to the user
      // alert('Speech recognition error: ' + event.error);
    };

    recognition.onend = () => {
      // When recognition ends, ensure voice input is no longer active
      console.log('Speech recognition ended.');
      streamlit.set({voice_input_active: false});
    };

    try {
        recognition.start();
        console.log('Speech recognition started.');
        // Set voice_input_active to true immediately when recording starts
        streamlit.set({voice_input_active: true});
    } catch (e) {
        console.error('Error starting speech recognition:', e);
        streamlit.set({voice_input_active: false});
        alert('Could not start speech recognition. Please check microphone permissions.');
    }
  });
}

// Check if the Python side has requested to start recording
if (streamlit.get('start_recording')) {
  streamlit.set('start_recording', false); // Reset the flag immediately
  startVoiceInput().then((transcript) => {
    if (transcript) {
      // If a transcript is received, set it as the prompt for the chat_input
      // This will trigger a rerun of the Streamlit app.
      streamlit.set({ 'prompt': transcript });
    }
  }).catch(error => {
    console.error('Voice input promise rejected:', error);
  });
}
"""

# Embed the JavaScript into the Streamlit app
st.markdown(f'<script>{voice_script}</script>', unsafe_allow_html=True)
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

    # Initialize OpenAI client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

    # --- UPDATED: Handle user input and OpenAI response, incorporating voice input ---
    # The chat_input value is now either typed by the user or set by the voice transcript
    prompt = st.chat_input("Your response", max_chars=1000, key="prompt")

    # Determine the label for the voice button based on recording status
    voice_button_label = "Stop Recording" if st.session_state.voice_input_active else "🎙️ Speak"

    # Create two columns for the chat input and voice button
    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        # If text is entered via chat_input, handle it
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            # No need to clear st.session_state.prompt here, chat_input handles it.

    with col2:
        # Button to trigger voice recording
        if st.button(voice_button_label, key="voice_trigger_button"):
            # This flag tells the JavaScript to start recording
            st.session_state.start_recording = True
            # The JavaScript will handle setting voice_input_active and voice_transcript

    # Handle voice transcript if it exists AFTER the `st.chat_input` has had a chance
    # to process its `prompt` value.
    if st.session_state.voice_transcript:
        # To prevent duplicates if the app reruns before the transcript is used
        # (e.g., if another action triggers a rerun before the user message is displayed)
        if not st.session_state.messages or st.session_state.messages[-1]["content"] != st.session_state.voice_transcript:
            st.session_state.messages.append({"role": "user", "content": st.session_state.voice_transcript})
            with st.chat_message("user"):
                st.markdown(st.session_state.voice_transcript)
        # Clear the transcript after it has been used to avoid reprocessing on next rerun
        st.session_state.voice_transcript = ""

    # Check for user messages (either typed or from voice) and get assistant response
    if st.session_state.user_message_count < 5:
        # Only fetch a new assistant response if the last message was from the user
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
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

            # Increment the user message count after the assistant responds
            st.session_state.user_message_count += 1

    # Check if the user message count reaches 5
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Show "Get Feedback"
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
        streamlit_js_eval(js_expressions="parent.window.location.reload()") # Use JS for a full page reload
