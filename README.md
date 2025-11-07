# PharmAI Backend

Welcome to the PharmAI Backend. This project is an **AI-powered assistant** for pharmaceutical analytics, built with Django and OpenAI.

It's designed to answer complex questions about pharmaceutical data by using a "Master Agent" that coordinates a team of specialized AI agents. This backend handles all the AI logic and streams answers back to a client application.

---

## What It Does

This system can answer questions and perform analysis on:

* **Market Intelligence:** Sales trends, competitor analysis (from IQVIA data).
* **Patent Landscapes:** Patent status and freedom-to-operate.
* **Clinical Trials:** Active trial data and sponsor info.
* **Trade Trends:** Export/Import (EXIM) data for drugs and APIs.
* **Internal Knowledge:** Summaries of your own company's documents.
* **Web Research:** Real-time web searches for news, papers, and guidelines.

---

## How It Works

The system is built around a **Master Agent** that acts like a project manager. When you send a query (e.g., "What is the market for drug X?"), the Master Agent coordinates a team of six specialist agents:

1.  **IQVIA Insights Agent**
2.  **Patent Landscape Agent**
3.  **Clinical Trials Agent**
4.  **EXIM Trade Agent**
5.  **Internal Knowledge Agent**
6.  **Web Intelligence Agent**

The agents work together to gather and analyze the data, and the system **streams the final, synthesized answer back to you in real-time** using Server-Sent Events (SSE).

---

## 🚀 Installation and Setup (Quickstart)

Follow these steps to get the backend running locally.

### 1. Download the Project

Download the project ZIP file by clicking on the ```Code``` button and unzip them to your chosen folder.

### 2. Create a Virtual Environment

Open a terminal in the project folder and run:

```bash
# For macOS/Linux
python -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\Activate.ps1
```
### 3. Install Dependencies

With your virtual environment active, install the required packages after opening the root directory (the one containing the manage.py file) in your terminal:
```
pip install -r requirements.txt
```
### 4. Configure Your Environment

This is the most important step. You must create a file named .env in the root of the project folder (the same place as manage.py).

Copy the following template, paste it into your new .env file, and add your API keys.
```
# --- REQUIRED ---
# Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here

# Get from [https://serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
SERPAPI_API_KEY=your_serpapi_key_here

# --- RECOMMENDED SETTINGS ---
MODEL_NAME=gpt-4
TEMPERATURE=0.7
MAX_TOKENS=2000

# --- Optional (for future use) ---
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=<model-name>
```
#### Important: The OPENAI_API_KEY and SERPAPI_API_KEY are required for the AI agents to function.

### 5. Set Up the Database
Run the initial database migrations:
```
python manage.py migrate
```

### 6. Run the Server
You're all set! Start the Django development server:
```
python manage.py runserver
```
Your backend is now running at ```http://127.0.0.1:8000/```

### Testing the API

You can quickly test the main streaming endpoint using curl in your terminal. Send a POST request with your query:
```
curl -X POST [http://127.0.0.1:8000/agent/stream/](http://127.0.0.1:8000/agent/stream/) \
     -H "Content-Type: application/json" \
     -d '{"query": "Give me IQVIA market trends for oncology drugs"}'
```
You will see a stream of JSON data ```(data: {"chunk": "..."})``` printed to your terminal as the AI generates the response.

### Key API Endpoints
The primary endpoint for interacting with the AI is:
```
POST /agent/stream/
```
This is the main endpoint you will use.

It accepts a JSON body: ```{"query": "Your question here"}```

It streams back the response in real-time.

Other endpoints like ```/agent/chat/ (for non-streaming responses) and /api/... (for specific data)``` also exist.

### Project Structure
```
pharmAI_backend/
├── API/                  # Handles domain-specific API logic (IQVIA, Patents, etc.)
├── ai_agent/             # The core AI, Master Agent, and specialist agent logic
├── backend/              # Main streaming endpoints and API routes
├── pharmAI_API/          # Core Django project settings
├── dataset.json          # Mock data for testing
├── db.sqlite3            # Your local database
├── manage.py             # Django's main script
├── requirements.txt      # Python dependencies
└── .env                  # (You must create this for your API keys)
```
