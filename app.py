import streamlit as st

from openai import OpenAI

from streamlit_js_eval import streamlit_js_eval

from streamlit_mic_recorder import mic_recorder

import os

import base64



# Setting up the Streamlit page configuration

st.set_page_config(page_title="Streamlit Interview Bot", page_icon="💬")

st.title("Interview Bot")



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

# New session state for controlling the flow after assistant response

if "awaiting_user_action" not in st.session_state:

    st.session_state.awaiting_user_action = False

# Session state to hold the AI's last spoken text and audio path

if "current_ai_response_text" not in st.session_state:

    st.session_state.current_ai_response_text = ""

if "current_ai_audio_path" not in st.session_state:

    st.session_state.current_ai_audio_path = ""

# Session state for feedback audio file path

if "feedback_audio_path" not in st.session_state:

    st.session_state.feedback_audio_path = ""





# Session state variables for initial personal information audio transcriptions

if "name_audio_transcription" not in st.session_state:

    st.session_state.name_audio_transcription = ""

if "experience_audio_transcription" not in st.session_state:

    st.session_state.experience_audio_transcription = ""

if "skills_audio_transcription" not in st.session_state:

    st.session_state.skills_audio_transcription = ""



# New session state for temporary voice input during the chat interview

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

                )

                audio_file.close()

                os.remove(temp_audio_file_path)



            setattr(st.session_state, f"{slot_name}_audio_transcription", transcript.text)

            st.write(f"**Transcription for {slot_name}:** {transcript.text}")

            st.session_state[slot_name] = transcript.text

            st.rerun()

    return getattr(st.session_state, f"{slot_name}_audio_transcription")





# --- Setup Stage ---

if not st.session_state.setup_complete:

    st.subheader('Personal Information')



    # Initialize session state for personal information

    if "name" not in st.session_state:

        st.session_state["name"] = ""

    if "experience" not in st.session_state:

        st.session_state["experience"] = ""

    if "skills" not in st.session_state:

        st.session_state["skills"] = ""

    if "job_post" not in st.session_state:

        st.session_state["job_post"] = ""





    # Option to input via text or voice

    input_method = st.radio("How would you like to provide your information?", ("Type", "Speak"), index=0, key="input_method_radio") #If you want to add Speak ad default option for Personal Data input - change to index 1 



    if input_method == "Type":

        st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40, key="name_text_input")

        st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200, key="experience_text_input")

        st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200, key="skills_text_input")

    else: # input_method == "Speak"

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



    # Company and Position Section

    st.subheader('Company and Position')



    # Initialize session state for company and position information

    if "position" not in st.session_state:

        st.session_state["position"] = ""

    if "company" not in st.session_state:

        st.session_state["company"] = ""



    # Replace dropdowns and radio buttons with text inputs

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





    # Button to complete setup

    if st.button("Start Interview", on_click=complete_setup, key="start_interview_button"):

        if not (st.session_state["name"] or st.session_state["experience"] or st.session_state["skills"]):

            st.warning("Please provide your personal information before starting the interview.")

            st.session_state.setup_complete = False

        else:

            st.write("Setup complete. Starting interview...")

            streamlit_js_eval(js_expressions="parent.window.location.reload()")





# --- Interview Phase ---

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:



    st.info(

    """

    **Interview Started!** Please introduce yourself.

    """,

    icon="🎤",

    )



    # Initialize OpenAI client

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])



    # Setting OpenAI model if not already initialized

    if "openai_model" not in st.session_state:

        st.session_state["openai_model"] = "gpt-4o"



    # Initializing the system prompt for the chatbot

    if not st.session_state.messages:

        # Construct the system prompt with the new job_post information

        system_prompt_content = (

            f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "

            f"with experience: {st.session_state['experience']} and skills: {st.session_state['skills']}. "

            f"You should interview him for the position {st.session_state['position']} "

            f"at the company {st.session_state['company']}."

        )

        # Conditionally add the job post information to the prompt

        if st.session_state["job_post"]:

            system_prompt_content += f" The job post description is as follows: {st.session_state['job_post']}."



        st.session_state.messages = [{

            "role": "system",

            "content": system_prompt_content

        }]



    # --- Display Past Messages (Text Only for History) ---

    st.subheader("Conversation History")

    for message in st.session_state.messages:

        if message["role"] == "user":

            st.markdown(f"**You:** {message['content']}")

        elif message["role"] == "assistant" and "content" in message:

            st.markdown(f"**Interviewer:** {message['content']}")

    st.markdown("---")



    # --- Interview Turn Logic ---



    # Case 1: Assistant has just responded, waiting for user to click "Continue"

    if st.session_state.awaiting_user_action:

        st.info("Please listen to the interviewer's response and click 'Next Question' when you're ready.")



        if st.session_state.current_ai_audio_path and os.path.exists(st.session_state.current_ai_audio_path):

            auto_play_audio(st.session_state.current_ai_audio_path)

        st.write(f"**Interviewer:** {st.session_state.current_ai_response_text}")



        if st.button("Next Question", key="continue_interview_button"):

            st.session_state.awaiting_user_action = False

            st.session_state.user_message_count += 1

            st.rerun()



    # Case 2: Ready for user input (either initial turn or after clicking "Continue")

    elif st.session_state.user_message_count < 5:

        st.subheader(f"Your Turn (Question {st.session_state.user_message_count + 1} of 5)")

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



    # Case 3: Interview is complete

    else:

        st.session_state.chat_complete = True





# --- Feedback and Restart ---

if st.session_state.chat_complete and not st.session_state.feedback_shown:

    if st.button("Get Feedback", on_click=show_feedback, key="get_feedback_button"):

        st.write("Fetching feedback...")



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

            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.

            Before the Feedback give a score of 1 to 10.

            Follow this format:

            Overall Score: //Your score

            Feedback: //Here you put your feedback

            Give only the feedback do not ask any additional questions.

            """},

            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: {conversation_history}"}

        ]

    )



    feedback_text = feedback_completion.choices[0].message.content

    st.write(feedback_text)

    

    # Generate and autoplay audio of the feedback

    feedback_audio_file = "feedback_summary.mp3"

    try:

        text_to_audio(feedback_client, feedback_text, feedback_audio_file, voice_type="alloy")

        st.session_state.feedback_audio_path = feedback_audio_file

        auto_play_audio(feedback_audio_file)

    except Exception as e:

        st.error(f"Error generating feedback audio: {e}. Displaying text only.")

        

    if st.button("Restart Interview", type="primary", key="restart_interview_button_final"):

        # Clean up all audio files on restart

        if st.session_state.feedback_audio_path and os.path.exists(st.session_state.feedback_audio_path):

            os.remove(st.session_state.feedback_audio_path)

        for message in st.session_state.messages:

            if message.get("audio_file_path") and os.path.exists(message["audio_file_path"]):

                os.remove(message["audio_file_path"])

        streamlit_js_eval(js_expressions="parent.window.location.reload()")
