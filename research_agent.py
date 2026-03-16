# ── Secrets ──────────────────────────────────────────────
from dotenv import load_dotenv
import os

# ── LangChain core ───────────────────────────────────────
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# ── OpenAI bridge ────────────────────────────────────────
from langchain_openai import ChatOpenAI

# ── Community tools ──────────────────────────────────────
from langchain_community.tools.tavily_search import TavilySearchResults

# ── LangGraph ────────────────────────────────────────────
from langgraph.prebuilt import create_react_agent

# ── Web scraping ─────────────────────────────────────────
import requests
from bs4 import BeautifulSoup

# ── Standard library ─────────────────────────────────────
import datetime
import json
import os as _os   # aliased to avoid conflict with 'import os' above

load_dotenv()


# ─────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────
search_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
)

@tool
def read_page(url: str) -> str:
    """Fetches the full text content of a webpage. Use this to read
    an article in detail after finding it via search."""
    try:
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup     = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:4000]
    except Exception as e:
        return f"Could not read page: {str(e)}"


# ─────────────────────────────────────────────────────────
# LLM CONNECTIONS
# ─────────────────────────────────────────────────────────
llm        = ChatOpenAI(model="gpt-4o-mini", temperature=0)
report_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
critic_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
chat_llm   = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

tools          = [search_tool, read_page]
research_agent = create_react_agent(model=llm, tools=tools)


# ─────────────────────────────────────────────────────────
# PROMPT CHAINS
# ─────────────────────────────────────────────────────────
report_prompt = ChatPromptTemplate.from_template("""
You are a professional research analyst. Using the research notes below,
write a clear, structured report on the topic: {topic}

Research notes:
{research}

Your report must include:
1. Executive summary (3-4 sentences)
2. Key findings (bullet points)
3. Important details and context
4. Limitations / what is still unknown
5. Sources referenced

Write in a professional but accessible tone.
""")
report_chain = report_prompt | report_llm

critic_prompt = ChatPromptTemplate.from_template("""
You are a critical research editor. Review this report and identify
weaknesses, gaps, or missing information.

Topic: {topic}
Draft report: {report}

Identify:
1. Missing angles or perspectives
2. Claims needing more evidence
3. Bias or one-sided viewpoints
4. Unanswered questions

Be specific. Maximum 300 words.
""")
critic_chain = critic_prompt | critic_llm

revision_prompt = ChatPromptTemplate.from_template("""
You are a professional research analyst. Revise your report on {topic}
based on this editor feedback.

Original report: {report}
Editor critique: {critique}

Rewrite addressing all critique points. Keep the same structure.
""")
revision_chain = revision_prompt | report_llm


# ═════════════════════════════════════════════════════════
# FEATURE 5 — STREAMING
# ═════════════════════════════════════════════════════════
def run_research_with_streaming(topic: str, stream_callback=None) -> str:
    research_query = f"""
    Research the following topic thoroughly: {topic}
    1. Search for recent and relevant information
    2. Read at least 2-3 full articles for depth
    3. Look for different perspectives and controversies
    4. Gather specific facts, numbers, and quotes
    5. Note all sources used
    Compile everything into detailed research notes.
    """

    for event in research_agent.stream(
        {"messages": [("human", research_query)]},
        stream_mode="updates",
    ):
        if "agent" in event:
            for msg in event["agent"].get("messages", []):
                content = msg.content
                if isinstance(content, str) and content.strip():
                    if stream_callback:
                        stream_callback(content[:120], "think")
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            name  = item.get("name", "")
                            inp   = item.get("input", {})
                            if "tavily" in name:
                                stream_callback and stream_callback(f"Searching: {inp.get('query','')}", "search")
                            elif name == "read_page":
                                stream_callback and stream_callback(f"Reading: {inp.get('url','')[:60]}...", "read")
                            else:
                                stream_callback and stream_callback(f"Using: {name}", "think")
        elif "tools" in event:
            for msg in event["tools"].get("messages", []):
                stream_callback and stream_callback(f"Got results from {getattr(msg,'name','tool')}", "done")

    result = research_agent.invoke({"messages": [("human", research_query)]})
    return result["messages"][-1].content


# ═════════════════════════════════════════════════════════
# FEATURE 9 — MULTI-AGENT CRITIC
# ═════════════════════════════════════════════════════════
def run_with_critic(topic, raw_research, max_rounds=2, stream_callback=None):
    critiques = []
    stream_callback and stream_callback("Writing first draft...", "think")

    current_report = report_chain.invoke({"topic": topic, "research": raw_research}).content

    for i in range(max_rounds):
        stream_callback and stream_callback(f"Critic reviewing draft {i+1}/{max_rounds}...", "think")
        critique = critic_chain.invoke({"topic": topic, "report": current_report}).content
        critiques.append(critique)

        stream_callback and stream_callback(f"Researcher revising (round {i+1})...", "think")
        current_report = revision_chain.invoke({
            "topic": topic, "report": current_report, "critique": critique
        }).content

    stream_callback and stream_callback("Multi-agent review complete!", "done")
    return current_report, critiques


# ═════════════════════════════════════════════════════════
# FEATURE 6 — FOLLOW-UP CHAT
# ═════════════════════════════════════════════════════════
def chat_with_report(user_message, report, topic, chat_history):
    system = SystemMessage(content=f"""
You are a helpful research assistant. You just researched "{topic}"
by searching the live internet. The report contains CURRENT information
from real websites — NOT old training data.
Today's date: {datetime.datetime.now().strftime("%B %d, %Y")}.

Report:
---
{report}
---

Answer from the report. Do NOT say your knowledge is limited to 2023.
If something isn't in the report say "The report doesn't cover that."
""")
    messages = [system]
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))
    return chat_llm.invoke(messages).content


# ─────────────────────────────────────────────────────────
# MAIN PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────────────────
def run_full_pipeline(topic, use_critic=True, critic_rounds=2, stream_callback=None):
    stream_callback and stream_callback("Starting research agent...", "think")
    raw_research = run_research_with_streaming(topic, stream_callback)

    if use_critic:
        stream_callback and stream_callback("Handing off to critic agent...", "think")
        final_report, critiques = run_with_critic(topic, raw_research, critic_rounds, stream_callback)
    else:
        final_report = report_chain.invoke({"topic": topic, "research": raw_research}).content
        critiques    = []

    return {"report": final_report, "critiques": critiques}


# ─────────────────────────────────────────────────────────
# SAVE REPORT — writes to a .md file
# ─────────────────────────────────────────────────────────
def save_report(topic: str, report: str) -> str:
    timestamp  = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = topic[:30].replace(" ", "_")
    filename   = f"report_{safe_topic}_{timestamp}.md"
    with open(filename, "w") as f:
        f.write(f"# Research Report: {topic}\n")
        f.write(f"*Generated on {datetime.datetime.now().strftime('%B %d, %Y')}*\n\n")
        f.write(report)
    return filename


# ═════════════════════════════════════════════════════════
# FEATURE B — RESEARCH HISTORY
#
# How history storage works:
# Every report is summarised and saved to research_history.json
# That JSON file is a list of dictionaries, one per research run.
# We read it when the sidebar loads, and write to it after each run.
#
# JSON is a plain text format — open research_history.json in
# VS Code after your first run and you'll see it clearly.
# ═════════════════════════════════════════════════════════

HISTORY_FILE = "research_history.json"


def save_to_history(topic: str, report: str, filename: str, critic_rounds: int = 0) -> None:
    """
    Saves a summary entry to research_history.json.
    We save metadata + a preview, NOT the full report text.
    The full report lives in the .md file referenced by filename.
    """
    entry = {
        "topic":         topic,
        # Human-readable timestamp for display
        "timestamp":     datetime.datetime.now().strftime("%b %d, %Y · %H:%M"),
        # ISO format timestamp for sorting and deleting by ID
        "timestamp_iso": datetime.datetime.now().isoformat(),
        "filename":      filename,
        "word_count":    len(report.split()),
        "critic_rounds": critic_rounds,
        # First 250 chars as a preview shown in the sidebar
        "preview":       report[:250].replace("\n", " ").strip() + "...",
    }

    history = load_history()

    # insert(0, x) adds x at the beginning of the list
    # so newest entries always appear first
    history.insert(0, entry)

    # Cap at 50 entries — history[:50] keeps only the first 50
    history = history[:50]

    # json.dump writes Python list → JSON file
    # indent=2 makes it human-readable with 2-space indentation
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_history() -> list:
    """
    Reads and returns the history list from JSON.
    Returns [] if the file doesn't exist yet.
    """
    if not _os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def load_report_from_file(filename: str) -> str:
    """
    Reads a saved .md report file and returns its text.
    """
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Report file '{filename}' was not found. It may have been deleted."


def delete_history_entry(timestamp_iso: str) -> None:
    """
    Removes one entry from history by its ISO timestamp.
    List comprehension keeps every entry EXCEPT the matching one.
    """
    history = load_history()
    history = [e for e in history if e.get("timestamp_iso") != timestamp_iso]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ─────────────────────────────────────────────────────────
# DIRECT TERMINAL RUN
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    topic = input("Enter a research topic: ")

    def print_cb(msg, step):
        icons = {"search": "🔍", "read": "📄", "think": "🧠", "done": "✅"}
        print(f"{icons.get(step,'•')} {msg}")

    result   = run_full_pipeline(topic, use_critic=True, critic_rounds=2, stream_callback=print_cb)
    filename = save_report(topic, result["report"])
    save_to_history(topic, result["report"], filename, critic_rounds=2)
    print("\n" + "="*60)
    print(result["report"])