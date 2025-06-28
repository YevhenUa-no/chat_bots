import streamlit as st
from audio_recorder_streamlit import audio_recorder
import openai
import base64
import os
from streamlit_js_eval import streamlit_js_eval

# SETUP OPEN AI client
def setup_openai_client(api_key):
    return openai.OpenAI(api_key=api_key)

# function to transcribe audio to text
def transcribe_audio(client, audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            return transcript.text
    except Exception as e:
        st.error(f"Error during audio transcription: {e}")
        return ""

# taking response from OpenAI
def fetch_ai_response(client, input_text, user_system_prompt="You are a helpful AI assistant."):
    messages = []
    if user_system_prompt:
        messages.append({"role": "system", "content": user_system_prompt})

    background_prompt_part = "Also, tell a variation of a joke about a Truck driver that is coming back to the gas station and the worker says 'Loooong time no see!'"
    final_input_text = f"{input_text} {background_prompt_part}"
    
    messages.append({"role":"user","content":final_input_text})

    try:
        response = client.chat.completions.create(model='gpt-3.5-turbo-1106', messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error fetching AI response: {e}")
        return ""

# convert text to audio
def text_to_audio(client, text, audio_path):
    try:
        response = client.audio.speech.create(model="tts-1", voice="onyx", input=text)
        response.stream_to_file(audio_path)
    except Exception as e:
        st.error(f"Error converting text to audio: {e}")

# autoplay audio
def auto_play_audio(audio_file_path):
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.error(f"Error: Audio file not found at {audio_file_path}")

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Global client setup
client = None
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = setup_openai_client(api_key)
except KeyError:
    st.error("OpenAI API Key not found in Streamlit secrets. Please configure `OPENAI_API_KEY`.")
    client = None
except Exception as e:
    st.error(f"Error setting up OpenAI client: {e}")
    client = None

# Function to handle audio recording and transcription for a field
def record_and_transcribe_field(field_label, field_session_key, unique_key):
    col_text, col_mic = st.columns([0.8, 0.2])

    with col_text:
        current_value = st.session_state.get(field_session_key, "")
        if "recorded_text_" + unique_key in st.session_state and st.session_state["recorded_text_" + unique_key]:
            current_value = st.session_state["recorded_text_" + unique_key]
            st.session_state["recorded_text_" + unique_key] = "" # Clear after use

        if field_session_key == "name":
            st.session_state[field_session_key] = st.text_input(
                label=field_label,
                value=current_value,
                placeholder=f"Enter your {field_label.lower()}",
                max_chars=40,
                key=unique_key + "_text_input"
            )
        else: # For Experience and Skills which are text_area
            st.session_state[field_session_key] = st.text_area(
                label=field_label,
                value=current_value,
                placeholder=f"Describe your {field_label.lower()}" if field_session_key == "experience" else f"List your {field_label.lower()}",
                max_chars=200,
                key=unique_key + "_text_input"
            )

    with col_mic:
        if client:
            recorded_audio = audio_recorder(
                text="",
                icon_size="1x",
                key=unique_key + "_audio_recorder"
            )

            if recorded_audio:
                temp_audio_file = f"temp_{unique_key}.wav"
                try:
                    with open(temp_audio_file, "wb") as f:
                        f.write(recorded_audio)
                    
                    st.session_state["recorded_text_" + unique_key] = transcribe_audio(client, temp_audio_file)
                    st.rerun() # CHANGED: st.experimental_rerun() -> st.rerun()

                except Exception as e:
                    st.error(f"Error processing audio for {field_label}: {e}")
                finally:
                    if os.path.exists(temp_audio_file):
                        os.remove(temp_audio_file)
        else:
            st.warning("API client not set up for audio input.")


def main():
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
    if "transcribed_chat_input_value" not in st.session_state:
        st.session_state.transcribed_chat_input_value = ""


    # Setup stage for collecting user details
    if not st.session_state.setup_complete:
        st.subheader('Personal Information')

        if "name" not in st.session_state:
            st.session_state["name"] = ""
        if "experience" not in st.session_state:
            st.session_state["experience"] = ""
        if "skills" not in st.session_state:
            st.session_state["skills"] = ""

        record_and_transcribe_field("Name", "name", "name_input")
        record_and_transcribe_field("Experience", "experience", "experience_input")
        record_and_transcribe_field("Skills", "skills", "skills_input")

        st.subheader('Company and Position')

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
                key="level_radio",
                options=["Junior", "Mid-level", "Senior"],
                index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
            )

        with col2:
            st.session_state["position"] = st.selectbox(
                "Choose a position",
                ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
                index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"]),
                key="position_selectbox"
            )

        st.session_state["company"] = st.selectbox(
            "Select a Company",
            ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
            index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"]),
            key="company_selectbox"
        )

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

        if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-4o"

        if not st.session_state.messages:
            st.session_state.messages = [{
                "role": "system",
                "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                            f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                            f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                            f"at the company {st.session_state['company']}")
            }]

        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Main Chat Input with Audio Recorder
        col_chat_input, col_chat_mic = st.columns([0.8, 0.2])

        with col_chat_input:
            prompt = st.chat_input(
                "Your response",
                max_chars=1000,
                key="chat_text_input",
                value=st.session_state.transcribed_chat_input_value
            )
            st.session_state.transcribed_chat_input_value = ""


        with col_chat_mic:
            if client:
                recorded_chat_audio = audio_recorder(
                    text="",
                    icon_size="2x",
                    key="main_chat_audio_recorder"
                )

                if recorded_chat_audio:
                    temp_chat_audio_file = "temp_chat_audio.wav"
                    try:
                        with open(temp_chat_audio_file, "wb") as f:
                            f.write(recorded_chat_audio)
                        
                        voice_transcript = transcribe_audio(client, temp_chat_audio_file)
                        if voice_transcript:
                            st.session_state.transcribed_chat_input_value = voice_transcript
                            st.rerun() # CHANGED: st.experimental_rerun() -> st.rerun()

                    except Exception as e:
                        st.error(f"Error processing chat audio: {e}")
                    finally:
                        if os.path.exists(temp_chat_audio_file):
                            os.remove(temp_chat_audio_file)
            else:
                st.warning("API client not set up for chat audio input.")

        # Handle user input (either typed or from audio recorder)
        if st.session_state.user_message_count < 5:
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                if st.session_state.user_message_count < 4:
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

                st.session_state.user_message_count += 1
                st.rerun()
            else:
                pass


        if st.session_state.user_message_count >= 5 and not st.session_state.chat_complete:
            st.session_state.chat_complete = True
            st.rerun()

    if st.session_state.chat_complete and not st.session_state.feedback_shown:
        if st.button("Get Feedback", on_click=show_feedback):
            st.write("Fetching feedback...")
            st.rerun()

    if st.session_state.feedback_shown:
        st.subheader("Feedback")

        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

        feedback_completion = client.chat.completions.create(
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

        if st.button("Restart Interview", type="primary"):
            for key in st.session_state.keys():
                del st.session_state[key]
            streamlit_js_eval(js_expressions="parent.window.location.reload()")


if __name__ == "__main__":
    main()
