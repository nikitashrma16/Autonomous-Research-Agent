# 🔍 Autonomous Research Agent

> An AI-powered multi-agent system that autonomously searches the live web, synthesizes findings into structured reports, refines them through a critic review loop, and lets you chat with your research — all in real time.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-awr--research--agent.streamlit.app-6c63ff?style=for-the-badge&logo=streamlit)](https://awr-research-agent.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-000000?style=for-the-badge)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai)](https://openai.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io)

---

## 📸 Demo

![Agent streaming its thoughts in real time while researching a topic]

> Type any topic → watch the agent search the web live → get a critic-reviewed, structured report → ask follow-up questions → download as PDF.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Live web search** | Searches the internet in real time via Tavily API — not training data |
| 🧠 **Live agent streaming** | Watch every search query, article read, and thought process as it happens |
| 🤖 **Multi-agent critic loop** | A second AI agent reviews the report for gaps and the researcher revises |
| 💬 **Follow-up chat (RAG)** | Ask questions about the report — answers grounded in what was researched |
| 📥 **PDF export** | Download a formatted PDF with cover page and critic feedback appendix |
| 🗂️ **Research history** | Every report saved locally — reload any past research instantly |
| 🔗 **Source cards** | All web sources displayed as clickable cards with domain labels |

---

## 🏗️ Architecture

```
User types topic
       │
       ▼
┌─────────────────────────────────┐
│      Research Agent             │  ← LangGraph ReAct loop
│  think → search → read → think  │  ← Tavily + BeautifulSoup
│  streams every step live        │  ← agent.stream()
└──────────────┬──────────────────┘
               │ raw research notes
               ▼
┌─────────────────────────────────┐
│      Critic Agent               │  ← critic_chain (LLM)
│  reviews draft for gaps         │
│  researcher revises (N rounds)  │  ← revision_chain (LLM)
└──────────────┬──────────────────┘
               │ final polished report
               ▼
┌─────────────────────────────────┐
│      Chat Agent (RAG)           │  ← report as system context
│  answers follow-up questions    │  ← full conversation history
│  grounded in the report         │
└─────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent framework** | LangGraph `create_react_agent` |
| **LLM** | OpenAI GPT-4o-mini |
| **Web search** | Tavily Search API |
| **Web scraping** | `requests` + `BeautifulSoup4` |
| **LLM orchestration** | LangChain Core (prompts, messages, tools) |
| **PDF generation** | fpdf2 |
| **Frontend** | Streamlit |
| **Data persistence** | JSON (research history) |
| **Secret management** | python-dotenv |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Tavily API key](https://tavily.com) (free tier: 1,000 searches/month)

### 1. Clone the repository

```bash
git clone https://github.com/nikitashrma16/Autonomous-Research-Agent.git
cd Autonomous-Research-Agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your API keys

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here
```

### 4. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
Autonomous-Research-Agent/
│
├── .env                    # API keys (never committed to git)
├── .gitignore              # excludes .env, __pycache__, history files
├── requirements.txt        # all Python dependencies with versions
│
├── research_agent.py       # core AI logic
│   ├── Tools               # search_tool, read_page
│   ├── LLM connections     # research, report, critic, chat
│   ├── Prompt chains       # report_chain, critic_chain, revision_chain
│   ├── run_research_with_streaming()   # Feature: live stream
│   ├── run_with_critic()               # Feature: multi-agent critic
│   ├── chat_with_report()              # Feature: RAG chat
│   ├── run_full_pipeline()             # main orchestrator
│   └── History functions               # Feature: research history
│
├── pdf_export.py           # PDF generation
│   ├── strip_markdown()    # Unicode sanitizer
│   ├── ResearchPDF class   # custom header + footer
│   └── generate_pdf()      # main export function
│
└── app.py                  # Streamlit UI
    ├── CSS styles          # dark theme, custom components
    ├── Sidebar             # settings, history, how-it-works
    ├── Input card          # topic input + example chips
    ├── Stream display      # live agent activity log
    ├── Results tabs        # report, sources, critic, chat
    └── Chat interface      # follow-up Q&A
```

---

## 📖 How It Works

### Step 1 — Research with live streaming

The research agent uses a **ReAct (Reasoning + Acting) loop** powered by LangGraph:

```
Thought:  "I should search for recent developments in fusion energy"
Action:   search_tool("fusion energy breakthroughs 2024")
Observe:  [5 search results returned]
Thought:  "I need more detail on result #2, let me read the full article"
Action:   read_page("https://example.com/fusion-article")
Observe:  [full article text returned]
Thought:  "I have enough information now"
Output:   [compiled research notes]
```

Every step streams to the UI in real time so you watch the agent work.

### Step 2 — Multi-agent critic loop

A second LLM agent reads the draft report and identifies:
- Missing perspectives or angles
- Claims that need more evidence
- Bias or one-sided viewpoints
- Unanswered questions

The researcher then rewrites based on this feedback. This repeats for N rounds (configurable 1-3).

### Step 3 — RAG follow-up chat

The full report is injected into the system prompt as context. When you ask follow-up questions, GPT answers **from the report** — not from its training data. The entire conversation history is passed with each message so context is maintained.

---

## ⚡ Key Technical Decisions

**`temperature=0` for the research agent**
Factual retrieval needs zero randomness. Deterministic output ensures consistent quality.

**`text[:4000]` hard cap on web scraping**
Uncapped page reading hits token limits and doubles API cost. 4,000 characters captures the article body; everything after is usually navigation and ads.

**`max_iterations=10` on the agent loop**
Without a cap, a confused agent loops indefinitely. 10 iterations handles every real research task tested.

**2 critic rounds as default**
Round 1 catches structural gaps. Round 2 catches what round 1 missed. Round 3 adds marginal quality improvement at double the cost.

**JSON for history storage**
No database setup required. Human-readable. Portable. Perfect for a single-user application.

**`encode('latin-1', 'replace')` as PDF safety net**
fpdf2's Helvetica font only supports Latin-1 characters. GPT regularly outputs Unicode (curly quotes, bullet symbols, em dashes). This catch-all converts anything unsupported to `?` instead of crashing.

---

## 🔧 Configuration

| Setting | Location | Default | Description |
|---|---|---|---|
| Enable critic | Sidebar toggle | On | Runs multi-agent review loop |
| Critic rounds | Sidebar slider | 2 | How many review + revision cycles |
| Max search results | `research_agent.py` | 5 | Results per Tavily query |
| Page reader limit | `research_agent.py` | 4000 chars | Max text extracted per article |
| History limit | `research_agent.py` | 50 entries | Max saved research sessions |

---

## 💰 Cost Estimate

| Operation | Approximate Cost |
|---|---|
| Single research run (no critic) | ~$0.02 |
| Single research run (2 critic rounds) | ~$0.05–0.08 |
| Follow-up chat message | ~$0.002 |
| PDF generation | Free (local) |

Costs vary based on topic complexity and how many articles the agent reads.

---

## 🚀 Deployment

This app is deployed on [Streamlit Cloud](https://share.streamlit.io).

To deploy your own instance:

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository, branch `main`, file `app.py`
5. Add your API keys in **Advanced Settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-your-key-here"
TAVILY_API_KEY = "tvly-your-key-here"
```

6. Click **Deploy**

---

## 📦 Requirements

```
langchain
langchain-openai
langchain-community
langchain-core
langgraph
tavily-python
python-dotenv
streamlit
requests
beautifulsoup4
fpdf2
```

---

## 🧠 What I Learned Building This

- How AI agents actually work — implementing the ReAct reasoning loop from scratch
- What RAG (Retrieval Augmented Generation) really means and how to build it properly
- Multi-agent system design — two AI agents collaborating and critiquing each other
- LangGraph streaming API for real-time UI updates
- Prompt engineering — how system prompts, temperature, and context shape LLM output
- Why LangChain imports keep breaking and how to manage package versions
- Unicode character handling in PDF generation
- Streamlit session state for persistent UI across reruns
- Deploying a Python AI app to production with secret management

---

## 👤 Author

**Nikita Sharma**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/nikitashrma16)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github)](https://github.com/nikitashrma16)

---

*Built from zero AI knowledge in 8 weeks. Every import error taught me something. Every crash made the code better.*
