## 🎙️ Streamlit Interview Bot
## A conversational AI interview coach that helps you prepare for your next big job opportunity. Built with Python, Streamlit, and the power of OpenAI's language and speech models.

![My GIF](https://raw.githubusercontent.com/YevhenUa-no/chat_bots/main/ME.gif) 


Streamlit page - https://chatbots-interview.streamlit.app/

Key Features
Voice-Powered Interface: Speak your answers and listen to the interviewer's questions, just like a real conversation.

Realistic AI Interviewer: Our bot acts as an HR executive, asking questions tailored to your specified role, company, and experience level.

Instant Feedback: Receive a score and detailed feedback on your performance after the interview is complete.

Easy to Use: A simple, interactive interface to guide you through the process.

# 🤖 Interview Bot – Flow Overview

## 📊 Text Flow


---

## 🟦 SETUP STAGE
- User provides personal info:
  - **Name**
  - **Experience**
  - **Skills**
  - **Company + Position**
  - *(Optional)* Job post description
- Info can be entered by:
  - Typing ✍️
  - Speaking 🎙️ (voice recorded + transcribed)
- Once all info is given → **Start Interview**



 │

 ▼

---

## 🟩 INTERVIEW STAGE
- AI Interviewer introduces itself
- **5 Question/Answer rounds**:
  - AI asks a question (text + audio 🔊)
  - User answers (text or voice 🎤)
  - AI responds with a follow-up
- User can also finish early → **Finish Interview**



 │
 ▼


---

## 🟨 FEEDBACK STAGE
- AI evaluates performance:
  - Gives **Score (1–10)**
  - Provides **Feedback summary**
- Feedback is available as:
  - Text 📄
  - Audio (autoplay 🔊)
- User options after feedback:
  - 🔄 Restart interview from scratch
  - ✏️ Restart with same inputs (edit details)


 │
 ▼
 END

---

## 🎨 Mermaid Flowchart


```mermaid
flowchart TD
    A([START]) --> B[🟦 Setup Stage]
    B -->|Provide info: Name, Experience, Skills, Company, Position, Job Post (optional)| C{Input Method}
    C -->|Typing ✍️| D[Text fields]
    C -->|Speaking 🎙️| E[Voice recording + transcription]
    D --> F[✅ Start Interview]
    E --> F[✅ Start Interview]

    F --> G[🟩 Interview Stage]
    G --> H[AI introduces itself]
    H --> I[Up to 5 Q&A rounds]
    I --> J[User can finish early → Finish Interview]
    J --> K[🟨 Feedback Stage]

    K --> L[Score (1–10) + Feedback summary]
    L --> M[Feedback available as Text 📄 + Audio 🔊]
    M --> N{Next Action}
    N -->|🔄 Restart from scratch| B
    N -->|✏️ Restart with same inputs| B
    N --> O([END ✅])



Credit for animation: https://brunopixels.tumblr.com/
