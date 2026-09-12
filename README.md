# LangGraph Chat Agent

A simple chat agent built with LangGraph and Groq.

## Setup

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   Add your Groq API key to `.env`:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

2. **Install Dependencies**:
   ```bash
   uv sync
   ```

## Running

Start the chat session:

```bash
uv run python main.py
```

Type `exit` or `quit` to leave the chat.
