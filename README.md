# 🤖 Webex Intelligent Agent

A Local-First AI Assistant that connects to your Webex Spaces, archives chat history, analyzes team interactions, and allows you to "Chat with your Data" using a secure local LLM (Llama 3).

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![AI](https://img.shields.io/badge/AI-Llama3-green)

## 🌟 Features

*   **Data Harvester:** Downloads full chat history from Webex Spaces (with Year filtering).
*   **Smart Analytics:** Visualizes Top Contributors and Activity Timelines.
*   **Auto-FAQ Generator:** Uses AI to identify questions in the chat and summarizes the answers into an Excel report.
*   **RAG Chatbot:** Chat with your specific project history using a Local LLM. Privacy-focused (data never leaves your machine).
*   **User Resolution:** Automatically maps User IDs to Real Names.

## 🛠️ Tech Stack

*   **Frontend:** Streamlit, Plotly
*   **Backend:** Python
*   **AI Engine:** Ollama (Llama 3), LangChain
*   **Database:** ChromaDB (Vector Store)

## 📋 Prerequisites

1.  **Python 3.9+**
2.  **Webex API Token:** Get it from [developer.webex.com](https://developer.webex.com/docs/getting-started).
3.  **Ollama:**
    *   Download from [ollama.com](https://ollama.com).
    *   Install the required models (run in terminal):
        ```bash
        ollama pull llama3
        ollama pull nomic-embed-text
        ```

## 🚀 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SambhuPNS/webex-smart-analyser.git
    cd webex-smart-analyser
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Mac/Linux
    # On Windows use: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ How to Run

1.  **Start the App:**
    ```bash
    streamlit run frontend.py
    ```

2.  **Using the App:**
    *   Enter your **Webex API Key** in the sidebar.
    *   Select a **Room** from the dropdown.
    *   Choose a **Date Range** (All History vs Specific Year).
    *   Click **Load Room Data**.

3.  **Explore:**
    *   **Chat Viewer Tab:** Search and filter raw messages.
    *   **Analytics Tab:** View charts and generate the **Q&A Excel Report**.
    *   **Chat Tab:** Ask questions like "Who fixed the login bug?" to the AI.

## 🔒 Privacy Note
All data (chat logs, vector database) is stored **locally** on your machine in the `data/` and `chroma_db_*/` folders. Nothing is uploaded to the cloud except the initial API call to fetch messages from Webex.

---
*Created by [Sreejish](https://github.com/sreejish05)*
