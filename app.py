import streamlit as st
import openai
from audiorecorder import audiorecorder
import os

# Set up the page title and OpenAI client
st.title("Voice Assistant Prototype")
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main app logic ---

# Use the audiorecorder component for voice input
audio = audiorecorder("Click to speak", "Listening...")

if len(audio) > 0:
    # Save the audio to a temporary file
    audio_file_path = "temp_audio.wav"
    audio.export(audio_file_path, format="wav")

    # Transcribe the audio using OpenAI's Whisper model
    with st.spinner("Transcribing..."):
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        user_prompt = transcript.text
        os.remove(audio_file_path) # Clean up the temporary file

    # Display user message in chat
    with st.chat_message("user"):
        st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Get a response from GPT
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True
            )
            
            # Stream the text response
            full_response = st.write_stream(response)

        # Convert the text response to speech using the text-to-speech API
        with st.spinner("Synthesizing speech..."):
            speech_response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=full_response,
            )
            
            # Save the audio and play it
            speech_file_path = "temp_speech.mp3"
            speech_response.stream_to_file(speech_file_path)
            st.audio(speech_file_path, format="audio/mp3", autoplay=True)
            os.remove(speech_file_path) # Clean up the temporary file

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
