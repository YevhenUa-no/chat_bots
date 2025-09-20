import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from streamlit_mic_recorder import mic_recorder
import os
import base64

# Setting up the Streamlit page configuration
st.set_page_config(page_title="Streamlit Interview Bot", page_icon="💬")
st.title("Interview Bot")

# --- Function to restart the interview ---
def restart_interview_with_initial_data():
    """Resets chat-related session state while preserving initial user input."""
    # Resetting session state variables for the chat and feedback
    st.session_state.user_message_count = 0
    st.session_state.feedback_shown = False
    st.session_state.chat_complete = False
    st.session_state.messages = []
    st.session_state.awaiting_user_action = False
    st.session_state.current_ai_response_text = ""
    st.session_state.current_ai_audio_path = ""
    st.session_state.feedback_audio_path = ""
    st.session_state.current_chat_voice_input = ""

    # Delete temporary audio files
    for filename in os.listdir():
        if filename.endswith(".mp3") or filename.endswith(".webm"):
            os.remove(filename)

    # Re-initialize the system prompt with the preserved user data
    system_prompt_content = (
        f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
        f"with experience: {st.session_state['experience']} and skills: {st.session_state['skills']}. "
        f"You should interview him for the position {st.session_state['position']} "
        f"at the company {st.session_state['company']}."
    )
    if st.session_state["job_post"]:
        system_prompt_content += f" The job post description is as follows: {st.session_state['job_post']}."

    st.session_state.messages = [{
        "role": "system",
        "content": system_prompt_content
    }]

    st.rerun()

# --- Initialize session state variables ---
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
if "awaiting_user_action" not in st.session_state:
    st.session_state.awaiting_user_action = False
if "current_ai_response_text" not in st.session_state:
    st.session_state.current_ai_response_text = ""
if "current_ai_audio_path" not in st.session_state:
    st.session_state.current_ai_audio_path = ""
if "feedback_audio_path" not in st.session_state:
    st.session_state.feedback_audio_path = ""
if "name_audio_transcription" not in st.session_state:
    st.session_state.name_audio_transcription = ""
if "experience_audio_transcription" not in st.session_state:
    st.session_state.experience_audio_transcription = ""
if "skills_audio_transcription" not in st.session_state:
    st.session_state.skills_audio_transcription = ""
if "current_chat_voice_input" not in st.session_state:
    st.session_state.current_chat_voice_input = ""

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# --- Convert text to audio ---
def text_to_audio(client, text, audio_path, voice_type="alloy"):
    try:
        response = client.audio.speech.create(model="tts-1", voice=voice_type, input=text)
        response.stream_to_file(audio_path)
    except Exception as e:
        st.error(f"Error converting text to audio: {e}")

# --- Autoplay audio ---
def auto_play_audio(audio_file_path):
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.error(f"Error: Audio file not found at {audio_file_path}")

# Function to handle audio recording and transcription for initial setup
def handle_audio_input_setup(slot_name, key):
    mic_recorder_output = mic_recorder(
        start_prompt="🎙️ Speak",
        stop_prompt="⏹️ Stop",
        just_once=True,
        use_container_width=True,
        key=key
    )

    if mic_recorder_output:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        audio_bytes = mic_recorder_output['bytes']
        if audio_bytes:
            temp_audio_file_path = f"audio_{slot_name}.webm"
            with open(temp_audio_file_path, "wb") as f:
                f.write(audio_bytes)

            with st.spinner(f"Transcribing {slot_name}..."):
                audio_file = open(temp_audio_file_path, "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
                audio_file.close()
                os.remove(temp_audio_file_path)

            setattr(st.session_state, f"{slot_name}_audio_transcription", transcript)
            st.write(f"**Transcription for {slot_name}:** {transcript}")
            st.session_state[slot_name] = transcript
            st.rerun()
    return getattr(st.session_state, f"{slot_name}_audio_transcription")

# --- Setup Stage ---
if not st.session_state.setup_complete:
    st.subheader('Personal Information')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""
    if "job_post" not in st.session_state:
        st.session_state["job_post"] = ""

    input_method = st.radio("How would you like to provide your information?", ("Type", "Speak"), index=0, key="input_method_radio")

    if input_method == "Type":
        st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40, key="name_text_input")
        st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=1500, key="experience_text_input")
        st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=1000, key="skills_text_input")
    else:
        st.write("### Name")
        current_name_transcription = handle_audio_input_setup("name", "mic_recorder_name")
        st.session_state["name"] = st.text_input(
            label="Name (from audio or manual edit)",
            value=st.session_state["name"] if st.session_state["name"] else current_name_transcription,
            placeholder="Enter your name or speak it", max_chars=40,
            key="name_input_final"
        )
        st.markdown("---")
        st.write("### Experience")
        current_experience_transcription = handle_audio_input_setup("experience", "mic_recorder_experience")
        st.session_state["experience"] = st.text_area(
            label="Experience (from audio or manual edit)",
            value=st.session_state["experience"] if st.session_state["experience"] else current_experience_transcription,
            placeholder="Describe your experience or speak it", max_chars=200,
            key="experience_input_final"
        )
        st.markdown("---")
        st.write("### Skills")
        current_skills_transcription = handle_audio_input_setup("skills", "mic_recorder_skills")
        st.session_state["skills"] = st.text_area(
            label="Skills (from audio or manual edit)",
            value=st.session_state["skills"] if st.session_state["skills"] else current_skills_transcription,
            placeholder="List your skills or speak them", max_chars=200,
            key="skills_input_final"
        )
        st.markdown("---")

    st.subheader('Company and Position')
    if "position" not in st.session_state:
        st.session_state["position"] = ""
    if "company" not in st.session_state:
        st.session_state["company"] = ""

    st.session_state["company"] = st.text_input(
        label="Company Name",
        value=st.session_state["company"],
        placeholder="e.g., Google",
        key="company_text_input"
    )
    st.session_state["position"] = st.text_input(
        label="Position Title",
        value=st.session_state["position"],
        placeholder="e.g., Senior Software Engineer",
        key="position_text_input"
    )
    st.session_state["job_post"] = st.text_area(
        label="Job Post Description (Optional)",
        value=st.session_state["job_post"],
        placeholder="Paste the job description here to help the interviewer ask more relevant questions.",
        max_chars=2000,
        key="job_post_text_area"
    )

    if st.button("Start Interview", on_click=complete_setup, key="start_interview_button"):
        if not (st.session_state["name"] and st.session_state["experience"] and st.session_state["skills"]):
            st.warning("Please provide your personal information before starting the interview.")
            st.session_state.setup_complete = False
        else:
            st.write("Setup complete. Starting interview...")
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

# --- Interview Phase ---
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state.messages:
        system_prompt_content = (
            f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
            f"with experience: {st.session_state['experience']} and skills: {st.session_state['skills']}. "
            f"You should interview him for the position {st.session_state['position']} "
            f"at the company {st.session_state['company']}."
        )
        if st.session_state["job_post"]:
            system_prompt_content += f" The job post description is as follows: {st.session_state['job_post']}."

        st.session_state.messages = [{
            "role": "system",
            "content": system_prompt_content
        }]

    # New: Auto-generate the first question and play audio if it's the start
    if st.session_state.user_message_count == 0 and not st.session_state.awaiting_user_action:
        with st.spinner("Preparing the first question..."):
            initial_greeting_prompt = (
                f"You are an HR executive from {st.session_state['company']} interviewing "
                f"a candidate named {st.session_state['name']} for the position of {st.session_state['position']}. "
                "Based on the candidate's skills and experience, ask the first interview question. "
                "Do not introduce yourself or the company again. Just provide the first question directly. "
                "Keep the tone welcoming and professional. A good example would be 'Tell me about a time you...' or 'How would you approach...'"
            )

            completion = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": "system", "content": initial_greeting_prompt},
                    {"role": "user", "content": f"Candidate's experience: {st.session_state['experience']}. Candidate's skills: {st.session_state['skills']}. Job post: {st.session_state['job_post']}"}
                ]
            )
            first_question = completion.choices[0].message.content

            speech_file_path = "assistant_response_0.mp3"
            try:
                text_to_audio(client, first_question, speech_file_path)
                st.session_state.current_ai_response_text = first_question
                st.session_state.current_ai_audio_path = speech_file_path
                st.session_state.awaiting_user_action = True
                st.session_state.messages.append({"role": "assistant", "content": first_question})
                st.rerun()
            except Exception as e:
                st.error(f"Error generating or playing speech: {e}. Falling back to text-only.")
                st.session_state.current_ai_response_text = first_question
                st.session_state.awaiting_user_action = True
                st.session_state.messages.append({"role": "assistant", "content": first_question})
                st.rerun()

    # Interview turn logic remains the same from here
    if st.session_state.awaiting_user_action:
        st.info("Please listen to the interviewer's response and click 'Next Question' when you're ready.")
        if st.session_state.current_ai_audio_path and os.path.exists(st.session_state.current_ai_audio_path):
            auto_play_audio(st.session_state.current_ai_audio_path)
        st.write(f"**Interviewer:** {st.session_state.current_ai_response_text}")

        if st.button("Next Question", key="continue_interview_button"):
            st.session_state.awaiting_user_action = False
            st.session_state.user_message_count += 1
            st.rerun()

    elif st.session_state.user_message_count < 5:
        st.subheader(f"Your Turn (Question {st.session_state.user_message_count + 1} of 5)")

        if st.session_state.user_message_count > 0: # Only display question for turns > 0
            # Get the last assistant message (the question) from the message history
            last_assistant_message = [msg for msg in st.session_state.messages if msg["role"] == "assistant"][-1]["content"]
            st.write(f"**Interviewer:** {last_assistant_message}")

        mic_recorder_chat_output = mic_recorder(
            start_prompt="🎙️ Speak your answer",
            stop_prompt="⏹️ Stop Recording",
            just_once=True,
            use_container_width=True,
            key=f"mic_recorder_chat_turn_{st.session_state.user_message_count}"
        )

        if mic_recorder_chat_output and mic_recorder_chat_output['bytes']:
            audio_bytes = mic_recorder_chat_output['bytes']
            temp_audio_file_path = "chat_audio_response.webm"
            with open(temp_audio_file_path, "wb") as f:
                f.write(audio_bytes)

            with st.spinner("Transcribing your answer..."):
                audio_file = open(temp_audio_file_path, "rb")
                transcribed_text = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
                audio_file.close()
                os.remove(temp_audio_file_path)

            st.session_state.current_chat_voice_input = transcribed_text
            st.rerun()

        user_prompt_input = st.text_area(
            "Your answer:",
            value=st.session_state.current_chat_voice_input,
            placeholder="Type your response here or speak it...",
            max_chars=1000,
            key=f"chat_text_area_{st.session_state.user_message_count}"
        )

        if st.button("Send Answer", key=f"send_answer_button_{st.session_state.user_message_count}"):
            if user_prompt_input:
                st.session_state.messages.append({"role": "user", "content": user_prompt_input})
                st.markdown(f"**You:** {user_prompt_input}")

                st.session_state.current_chat_voice_input = ""

                if st.session_state.user_message_count < 5:
                    with st.spinner("Interviewer is thinking..."):
                        stream = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                            ],
                            stream=True,
                        )
                        response_text = ""
                        response_placeholder = st.empty()
                        for chunk in stream:
                            if chunk.choices[0].delta.content is not None:
                                response_text += chunk.choices[0].delta.content
                                response_placeholder.markdown(f"**Interviewer:** {response_text}")

                        speech_file_path = f"assistant_response_{st.session_state.user_message_count}.mp3"
                        try:
                            text_to_audio(client, response_text, speech_file_path, voice_type="alloy")

                            st.session_state.messages.append({"role": "assistant", "content": response_text, "audio_file_path": speech_file_path})
                            st.session_state.current_ai_response_text = response_text
                            st.session_state.current_ai_audio_path = speech_file_path
                            st.session_state.awaiting_user_action = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating or playing speech: {e}. Falling back to text-only.")
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
                            st.session_state.awaiting_user_action = False
                            st.session_state.user_message_count += 1
                            st.rerun()
                else:
                    st.session_state.chat_complete = True
                    st.rerun()
            else:
                st.warning("Please provide an answer before sending.")

        if st.button("Finish Interview and Get Feedback", key="finish_interview_button"):
            st.session_state.chat_complete = True
            st.session_state.awaiting_user_action = False
            st.rerun()
    else:
        st.session_state.chat_complete = True

# --- Feedback and Restart ---
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback, key="get_feedback_button"):
        st.write("Fetching feedback...")
    st.button("Restart Interview", key="restart_before_feedback_button", on_click=restart_interview_with_initial_data)

if st.session_state.feedback_shown:
    st.subheader("Feedback")
    feedback_messages_for_llm = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages if msg["role"] != "system"
    ]
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in feedback_messages_for_llm])
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an evaluation tool that provides structured, constructive feedback on an interviewee’s performance.
                ... (rest of the system prompt)
                """
            },
            {
                "role": "user",
                "content": f"Here is the interview transcript to evaluate: {conversation_history}"
            }
        ]
    )
    feedback_text = feedback_completion.choices[0].message.content
    st.write(feedback_text)
    feedback_audio_file = "feedback_summary.mp3"
    try:
        text_to_audio(feedback_client, feedback_text, feedback_audio_file, voice_type="alloy")
        st.session_state.feedback_audio_path = feedback_audio_file
        auto_play_audio(feedback_audio_file)
    except Exception as e:
        st.error(f"Error generating feedback audio: {e}. Displaying text only.")

    if st.button("Restart Interview", type="primary", key="restart_interview_button_final"):
        restart_interview_with_initial_data()
