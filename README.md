## 🎙️ Streamlit Interview Bot
## A conversational AI interview coach that helps you prepare for your next big job opportunity. Built with Python, Streamlit, and the power of OpenAI's language and speech models.

![My GIF](https://raw.githubusercontent.com/YevhenUa-no/chat_bots/main/ME.gif) 


Streamlit page - https://chatbots-interview.streamlit.app/

## Features

-   Voice and text input
-   AI-powered questions
-   Interview performance feedback

Easy to Use: A simple, interactive interface to guide you through the process.


 ## User Flow

This diagram illustrates the user's journey through the application.

```mermaid
flowchart LR
    A([START]) --> B[Setup Stage]
    B --> C{Input Method}
    C --> D[Typing]
    C --> E[Speaking and Transcription]
    D --> F[Start Interview]
    E --> F[Start Interview]

    F --> G[Interview Stage]
    G --> H[AI introduces]
    H --> I[Up to 5 Q & A rounds]
    I --> J[Finish Interview option]

    J --> K[Feedback Stage]
    K --> L[Score and Feedback]
    L --> M[Feedback as Text or Audio]
    M --> N{Next Action}
    N --> O[Restart from scratch]
    N --> P[Restart with same inputs]
    O --> B
    P --> B
    N --> Q([END])
```


# 🤖 Interview Bot – Flow Overview


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




---

## 🟩 INTERVIEW STAGE
- AI Interviewer introduces itself
- **5 Question/Answer rounds**:
  - AI asks a question (text + audio 🔊)
  - User answers (text or voice 🎤)
  - AI responds with a follow-up
- User can also finish early → **Finish Interview**




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

