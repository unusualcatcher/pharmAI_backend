"""
AI Agent Configuration Module

This module loads all environment variables and initializes LLM instances
that will be used across all agents. It runs once when Django starts.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Set them in os.environ for LangChain to access
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

# Model Configuration
OPENAI_MODEL = os.getenv('MODEL_NAME', 'gpt-4')
GEMINI_MODEL = os.getenv("GEMINI_MODEL", 'gemini-pro')
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2000'))

# ============================================================
# LLM INSTANCES
# ============================================================

# Regular LLM (for planning and tool selection)
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS
)

# Streaming LLM (for final synthesis and streaming responses)
streaming_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
    streaming=True  # This enables streaming
)

print("AI Agent Configuration Loaded Successfully")
print(f"   - OpenAI Model: {OPENAI_MODEL}")
print(f"   - Temperature: {TEMPERATURE}")
print(f"   - Max Tokens: {MAX_TOKENS}")