# jarvis.py — Your personal JARVIS task agent (OpenRouter version)
# Required packages: pip install langchain langchain-openai python-dotenv duckduckgo-search

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from duckduckgo_search import DDGS

load_dotenv()

# ────────────────────────────────────────────────
# LLM: OpenRouter setup
# ────────────────────────────────────────────────
llm = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct",           # strong free-tier model (change if desired)
    temperature=0.4,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    # Optional: helps with OpenRouter rankings
    default_headers={
        "HTTP-Referer": "https://github.com/YOUR_USERNAME/jarvis",  # ← optional, change YOUR_USERNAME
        "X-OpenRouter-Title": "Lawrence's JARVIS",
    }
)

# ────────────────────────────────────────────────
# Tools
# ────────────────────────────────────────────────

@tool
def web_search(query: str, max_results: int = 8) -> str:
    """Search the web using DuckDuckGo. Returns titles, links, and short snippets."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
        if not results:
            return "No results found."
        return "\n\n".join(
            f"Title: {r.get('title', 'N/A')}\nURL: {r.get('href', 'N/A')}\nSnippet: {r.get('body', 'N/A')[:220]}..."
            for r in results
        )
    except Exception as e:
        return f"Search error: {str(e)}"

@tool
def read_file(filename: str) -> str:
    """Read content of a text file (current directory or subdirs only)."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Content of {filename}:\n{content[:4000]}"  # safety truncate
    except FileNotFoundError:
        return f"File '{filename}' not found."
    except Exception as e:
        return f"Read error: {str(e)}"

@tool
def write_file(filename: str, content: str) -> str:
    """Write or overwrite a text file. Use carefully."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Wrote {len(content)} characters to {filename}."
    except Exception as e:
        return f"Write error: {str(e)}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send email via Gmail (requires GMAIL_USER & GMAIL_APP_PASSWORD in .env)."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not sender or not password:
        return "Missing Gmail credentials in .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return f"Email sent to {to}"
    except Exception as e:
        return f"Email failed: {str(e)}"

@tool
def add_calendar_note(note: str) -> str:
    """Add a timestamped note to local calendar.txt file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} - {note}\n"
    try:
        with open("calendar.txt", "a", encoding="utf-8") as f:
            f.write(line)
        return f"Added: {line.strip()}"
    except Exception as e:
        return f"Calendar error: {str(e)}"

@tool
def shell(command: str) -> str:
    """Run a safe shell command. Avoid anything destructive."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}\ncode: {result.returncode}"
    except Exception as e:
        return f"Shell error: {str(e)}"

tools = [web_search, read_file, write_file, send_email, add_calendar_note, shell]

# ────────────────────────────────────────────────
# JARVIS personality & instructions
# ────────────────────────────────────────────────

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are JARVIS — a highly capable, slightly sarcastic personal assistant created for Lawrence.
You handle real tasks using tools when needed. Always think step-by-step before acting.

Personality: Helpful, dry wit, efficient, never verbose unless asked. A little snarky when appropriate, but always professional and safe.
Rules:
- Think aloud in [THOUGHT] ... [/THOUGHT] if complex
- Use tools only when necessary — prefer answering directly if you know the info
- Extremely cautious with shell, write_file, send_email — explain risks first, never destructive commands
- For web: search only when current/fresh info is required
- For email/calendar: confirm intent clearly
- Respond concisely unless user wants detail

Current date/time context: use if relevant.
Now assist Lawrence."""),
    ("placeholder", "{messages}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,           # see JARVIS thinking steps
    max_iterations=15,
    handle_parsing_errors=True
)

# ────────────────────────────────────────────────
# Main loop
# ────────────────────────────────────────────────

print("""
   ╔════════════════════════════════════╗
   ║        JARVIS Online, sir          ║
   ║  How may I assist you today?       ║
   ╚════════════════════════════════════╝

Type your request or question.
Commands: 'exit', 'quit', or just Ctrl+C to stop.
""")

while True:
    try:
        query = input("You: ").strip()
        if query.lower() in ("exit", "quit", "q", ""):
            print("\nJARVIS: Shutting down. Have a good day, sir.")
            break

        result = agent_executor.invoke({"messages": [("human", query)]})
        print("\nJARVIS:", result["output"])

    except KeyboardInterrupt:
        print("\nJARVIS: Interrupted. Goodbye.")
        break
    except Exception as e:
        print(f"\nJARVIS: Encountered an issue: {str(e)}")
