import streamlit as st
import datetime
import re

# ── Our own files ─────────────────────────────────────────
from research_agent import (
    run_full_pipeline,
    chat_with_report,
    save_report,
    save_to_history,       # Feature B
    load_history,          # Feature B
    load_report_from_file, # Feature B
    delete_history_entry,  # Feature B
)
from pdf_export import generate_pdf   # Feature C

# ─────────────────────────────────────────────────────────
# PAGE CONFIG — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif;
    color: #e8e6e0;
}
[data-testid="stAppViewContainer"] > .main { background-color: #0a0a0f !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.block-container { padding-top: 2rem !important; max-width: 960px; }

[data-testid="stSidebar"] {
    background-color: #0f0f18 !important;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] * { color: #a0a0b8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e8e6e0 !important;
    font-family: 'Syne', sans-serif !important;
}

.hero { text-align: center; padding: 2.5rem 0 1.5rem; }
.hero-badge {
    display: inline-block; font-size: 11px; font-weight: 500;
    letter-spacing: 0.15em; text-transform: uppercase; color: #6c63ff;
    background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.25);
    border-radius: 20px; padding: 5px 14px; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Syne', sans-serif; font-size: 2.8rem; font-weight: 800;
    color: #ffffff; margin: 0 0 0.6rem; letter-spacing: -0.02em; line-height: 1.1;
}
.hero-title span {
    background: linear-gradient(135deg,#6c63ff,#a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub { font-size: 1rem; color: #6b6b80; font-weight: 300; max-width: 500px; margin: 0 auto; line-height: 1.6; }

.card { background: #0f0f18; border: 1px solid #1e1e2e; border-radius: 16px; padding: 1.75rem; margin: 1.5rem 0; }

[data-testid="stTextInput"] input {
    background-color: #13131f !important; border: 1px solid #2a2a3e !important;
    border-radius: 10px !important; color: #e8e6e0 !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 1rem !important; padding: 0.75rem 1rem !important;
}
[data-testid="stTextInput"] input:focus { border-color: #6c63ff !important; box-shadow: 0 0 0 3px rgba(108,99,255,0.12) !important; }
[data-testid="stTextInput"] input::placeholder { color: #3a3a55 !important; }
[data-testid="stTextInput"] label {
    color: #a0a0b8 !important; font-size: 0.85rem !important;
    font-weight: 500 !important; letter-spacing: 0.05em !important; text-transform: uppercase !important;
}

[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg,#6c63ff,#8b5cf6) !important;
    border: none !important; border-radius: 10px !important; color: white !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    font-size: 0.95rem !important; width: 100% !important;
}
[data-testid="baseButton-primary"]:hover { opacity: 0.9 !important; }
[data-testid="baseButton-primary"]:disabled { background: #1e1e2e !important; color: #3a3a55 !important; }
[data-testid="baseButton-secondary"] {
    background: transparent !important; border: 1px solid #2a2a3e !important;
    border-radius: 10px !important; color: #a0a0b8 !important;
    font-family: 'DM Sans', sans-serif !important; width: 100% !important;
}
[data-testid="baseButton-secondary"]:hover { border-color: #6c63ff !important; color: #e8e6e0 !important; }

.stream-box {
    background: #080810; border: 1px solid #1e1e2e; border-radius: 12px;
    padding: 1.25rem; font-family: 'DM Sans', sans-serif; font-size: 0.82rem;
    max-height: 300px; overflow-y: auto;
}
.stream-row { display: flex; align-items: flex-start; gap: 10px; padding: 5px 0; border-bottom: 1px solid #12121e; }
.stream-row:last-child { border-bottom: none; }
.stream-icon { font-size: 13px; flex-shrink: 0; margin-top: 1px; }
.stream-text { color: #7a7a90; line-height: 1.4; }
.stream-text.search { color: #6c63ff; }
.stream-text.read   { color: #5DCAA5; }
.stream-text.think  { color: #888780; }
.stream-text.done   { color: #4ade80; }

.report-card { background: #0f0f18; border: 1px solid #1e1e2e; border-radius: 16px; padding: 2.25rem; margin-top: 1.5rem; }
.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1.25rem; border-bottom: 1px solid #1e1e2e; }
.report-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; color: #fff; }
.report-meta { font-size: 0.78rem; color: #3a3a55; }

.stats-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 1.25rem; }
.stat-chip { background: #13131f; border: 1px solid #1e1e2e; border-radius: 8px; padding: 5px 12px; font-size: 0.78rem; color: #6b6b80; }
.stat-chip span { color: #a78bfa; font-weight: 500; }

.success-banner {
    background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.2);
    border-radius: 10px; padding: 0.7rem 1.2rem; font-size: 0.875rem; color: #4ade80; margin-bottom: 1.25rem;
}
.critique-box { background: rgba(234,90,48,0.06); border: 1px solid rgba(234,90,48,0.2); border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1rem; }
.critique-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #D85A30; margin-bottom: 6px; }
.critique-text { font-size: 0.82rem; color: #a0997a; line-height: 1.6; }

/* Feature D — Source cards */
.source-card {
    background: #0d0d18; border: 0.5px solid #1e1e2e; border-radius: 10px;
    padding: 12px 14px; margin-bottom: 8px; transition: border-color 0.15s;
}
.source-card:hover { border-color: #6c63ff; }
.source-domain { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #6c63ff; margin-bottom: 4px; }
.source-url { font-size: 0.78rem; color: #4a4a65; word-break: break-all; }
.source-url a { color: #5a5a80; text-decoration: none; }
.source-url a:hover { color: #a78bfa; }

/* Feature B — History cards in sidebar */
.hist-card {
    background: #13131f; border: 0.5px solid #1e1e2e; border-radius: 8px;
    padding: 10px 12px; margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s;
}
.hist-card:hover { border-color: #2a2a3e; }
.hist-topic { font-size: 12px; font-weight: 500; color: #c0bdb5; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-meta  { font-size: 10px; color: #3a3a55; }

.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { font-family: 'Syne', sans-serif !important; color: #fff !important; }
.stMarkdown p,.stMarkdown li { color: #c0bdb5 !important; }
.stMarkdown strong { color: #e8e6e0 !important; }
.stMarkdown code { background: #13131f !important; border: 1px solid #2a2a3e !important; color: #a78bfa !important; border-radius: 4px !important; padding: 2px 6px !important; }
.stMarkdown a { color: #6c63ff !important; }

[data-testid="stTabs"] button { font-family: 'DM Sans', sans-serif !important; color: #6b6b80 !important; font-size: 0.875rem !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #e8e6e0 !important; }
[data-testid="stExpander"] { background: #0d0d16 !important; border: 1px solid #1e1e2e !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #6b6b80 !important; font-size: 0.85rem !important; }
[data-testid="stSlider"] > div > div > div { background-color: #6c63ff !important; }
[data-testid="stChatMessage"] { background: #0f0f18 !important; border: 1px solid #1e1e2e !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# FEATURE D — SOURCE CARD HELPER
#
# What is this?
# After the report is generated, we scan the text for URLs
# using a regular expression (regex). Each URL found gets
# displayed as a clickable card below the report.
#
# What is regex?
# A regex pattern is a search template for text.
# re.findall(pattern, text) returns a list of all matches.
# The pattern below matches any text starting with http://
# or https:// and continuing until a space or newline.
# ═════════════════════════════════════════════════════════
def extract_sources(report: str) -> list:
    """
    Finds all URLs in the report text.
    Returns a list of unique URL strings.
    """
    # This regex pattern matches URLs:
    #   https?  — http or https (? means the s is optional)
    #   ://     — literal colon-slash-slash
    #   [^\s)]+ — one or more chars that are NOT space or )
    pattern = r'https?://[^\s)]+'
    urls    = re.findall(pattern, report)

    # dict.fromkeys() removes duplicates while preserving order.
    # It's like a set() but keeps the original order.
    unique_urls = list(dict.fromkeys(urls))
    return unique_urls


def get_domain(url: str) -> str:
    """
    Extracts just the domain name from a full URL.
    e.g. "https://www.reuters.com/article/123" → "reuters.com"
    """
    try:
        # split("//") splits on "//"  → ["https:", "www.reuters.com/article/123"]
        # [1] takes the second part   → "www.reuters.com/article/123"
        # split("/")[0] takes before / → "www.reuters.com"
        # replace("www.", "") removes www. prefix
        domain = url.split("//")[1].split("/")[0].replace("www.", "")
        return domain
    except Exception:
        return url


def render_source_cards(urls: list) -> None:
    """
    Renders a grid of source cards in Streamlit.
    Each card shows the domain name and a clickable URL.
    """
    if not urls:
        st.markdown(
            '<div style="color:#3a3a55;font-size:0.85rem">No URLs found in this report.</div>',
            unsafe_allow_html=True
        )
        return

    # st.columns(3) creates 3 equal-width columns side by side.
    # We fill them in rotation using index % 3.
    # % is the modulo operator — it gives the remainder of division.
    # So for 7 URLs: indices 0,1,2 → cols 0,1,2; then 3,4,5 → cols 0,1,2; then 6 → col 0
    cols = st.columns(3)
    for i, url in enumerate(urls):
        domain = get_domain(url)
        with cols[i % 3]:
            st.markdown(f"""
            <div class="source-card">
                <div class="source-domain">{domain}</div>
                <div class="source-url"><a href="{url}" target="_blank">{url[:65]}{'...' if len(url)>65 else ''}</a></div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
#
# Streamlit reruns the entire script on every interaction.
# Session state persists across reruns — like a global
# variable that survives page refreshes within the same session.
# ─────────────────────────────────────────────────────────
defaults = {
    "report":       None,
    "critiques":    [],
    "topic":        "",
    "filename":     "",
    "timestamp":    "",
    "stream_log":   [],
    "chat_history": [],
    "running":      False,
    # Feature B — tracks which history entry is loaded
    "loaded_from_history": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ═════════════════════════════════════════════════════════
# FEATURE B — SIDEBAR HISTORY
#
# load_history() reads research_history.json and returns
# a list of past report summaries. We display each one
# as a clickable card in the sidebar.
#
# When clicked, we load the .md file and display it in
# the main panel — without re-running the agent.
# ═════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### How it works")
    steps = [
        ("Search", "Agent queries Tavily for live web results"),
        ("Stream", "Watch every step live as it happens"),
        ("Critique", "Second AI agent finds gaps in the report"),
        ("Revise", "Researcher rewrites based on feedback"),
        ("Chat", "Ask follow-up questions about the report"),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(f"""
        <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #1e1e2e">
            <div style="width:20px;height:20px;background:rgba(108,99,255,0.15);
                border:1px solid rgba(108,99,255,0.3);border-radius:50%;display:flex;
                align-items:center;justify-content:center;font-size:10px;font-weight:700;
                color:#6c63ff;flex-shrink:0">{i}</div>
            <div style="font-size:0.82rem;line-height:1.5;color:#6b6b80">
                <strong style="color:#a0a0b8;display:block">{title}</strong>{desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Settings")

    use_critic = st.toggle("Enable multi-agent critic", value=True)
    critic_rounds = 2
    if use_critic:
        critic_rounds = st.slider("Critic rounds", 1, 3, 2)

    # ── Research History ──────────────────────────────────
    st.markdown("---")
    st.markdown("### Research history")

    history = load_history()

    if not history:
        st.markdown(
            '<div style="font-size:0.8rem;color:#3a3a55">No history yet. Run your first research!</div>',
            unsafe_allow_html=True
        )
    else:
        # Show a card for each past research run
        for entry in history:
            col_card, col_del = st.columns([5, 1])

            with col_card:
                # st.button returns True when clicked.
                # We use the topic as the button label.
                # key= must be unique for each button —
                # we use the ISO timestamp as a unique identifier.
                if st.button(
                    entry["topic"][:35] + ("..." if len(entry["topic"]) > 35 else ""),
                    key=f"hist_{entry['timestamp_iso']}",
                    use_container_width=True,
                ):
                    # Load the full report from the .md file
                    loaded = load_report_from_file(entry["filename"])

                    # Populate session state so the main panel displays it
                    st.session_state.report    = loaded
                    st.session_state.topic     = entry["topic"]
                    st.session_state.filename  = entry["filename"]
                    st.session_state.timestamp = entry["timestamp"]
                    st.session_state.critiques = []
                    st.session_state.chat_history = []
                    st.session_state.loaded_from_history = True

                    # st.rerun() forces Streamlit to re-run the script
                    # immediately, picking up the new session_state values
                    st.rerun()

                st.markdown(
                    f'<div style="font-size:10px;color:#3a3a55;margin-top:-8px;padding-bottom:4px">'
                    f'{entry["timestamp"]} · {entry["word_count"]:,} words</div>',
                    unsafe_allow_html=True
                )

            with col_del:
                # Small delete button — removes from history JSON
                if st.button("✕", key=f"del_{entry['timestamp_iso']}"):
                    delete_history_entry(entry["timestamp_iso"])
                    st.rerun()


# ─────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">GPT-4o-mini · LangGraph · Tavily · Multi-Agent</div>
    <div class="hero-title">Autonomous <span>Research</span> Agent</div>
    <div class="hero-sub">Type a topic. Watch the agent think live.
    Get a critic-reviewed, structured report.</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# INPUT CARD
# ─────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
topic = st.text_input(
    "Research topic",
    placeholder="e.g.  Latest breakthroughs in quantum computing",
)
examples = ["AI in drug discovery 2024", "State of nuclear fusion", "How CRISPR works", "Future of EVs"]
st.markdown(
    '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:0.75rem">' +
    "".join(f'<span style="background:#13131f;border:1px solid #2a2a3e;border-radius:20px;'
            f'padding:4px 12px;font-size:0.78rem;color:#6b6b80">{e}</span>' for e in examples) +
    "</div>", unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# RUN BUTTON
# ─────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_clicked = st.button(
        "Start Research",
        type="primary",
        disabled=not topic or st.session_state.running,
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────
# AGENT EXECUTION
# ─────────────────────────────────────────────────────────
if run_clicked and topic:
    # Reset previous run
    st.session_state.stream_log            = []
    st.session_state.report                = None
    st.session_state.critiques             = []
    st.session_state.chat_history          = []
    st.session_state.loaded_from_history   = False
    st.session_state.running               = True

    st.markdown("---")
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:700;color:#fff;margin-bottom:0.75rem">Live agent activity</div>', unsafe_allow_html=True)

    stream_placeholder = st.empty()

    def stream_callback(message: str, step_type: str):
        """
        Called by research_agent.py for each agent update.
        Rebuilds the live log HTML and updates the placeholder.
        """
        icons = {"search": ("🔍", "search"), "read": ("📄", "read"), "think": ("🧠", "think"), "done": ("✅", "done")}
        icon, css_class = icons.get(step_type, ("•", "think"))
        st.session_state.stream_log.append({"icon": icon, "text": message, "class": css_class})

        rows_html = "".join(
            f'<div class="stream-row"><span class="stream-icon">{e["icon"]}</span>'
            f'<span class="stream-text {e["class"]}">{e["text"]}</span></div>'
            for e in st.session_state.stream_log
        )
        stream_placeholder.markdown(f'<div class="stream-box">{rows_html}</div>', unsafe_allow_html=True)

    try:
        result = run_full_pipeline(
            topic=topic,
            use_critic=use_critic,
            critic_rounds=critic_rounds,
            stream_callback=stream_callback,
        )

        st.session_state.report    = result["report"]
        st.session_state.critiques = result["critiques"]
        st.session_state.topic     = topic
        st.session_state.filename  = save_report(topic, result["report"])
        st.session_state.timestamp = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")

        # Feature B — save to history after every successful run
        save_to_history(
            topic=topic,
            report=result["report"],
            filename=st.session_state.filename,
            critic_rounds=len(result["critiques"]),
        )

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
    finally:
        st.session_state.running = False


# ─────────────────────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────────────────────
if st.session_state.report:

    report    = st.session_state.report
    topic_s   = st.session_state.topic
    filename  = st.session_state.filename
    ts        = st.session_state.timestamp
    critiques = st.session_state.critiques

    st.markdown("---")

    # Show a different banner if loaded from history
    if st.session_state.loaded_from_history:
        st.markdown(f"""
        <div style="background:rgba(108,99,255,0.08);border:1px solid rgba(108,99,255,0.2);
             border-radius:10px;padding:0.7rem 1.2rem;font-size:0.875rem;color:#a78bfa;margin-bottom:1.25rem">
            📂 &nbsp; Loaded from history — {ts}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="success-banner">
            ✓ &nbsp; Research complete — {ts}
            {"&nbsp;·&nbsp; " + str(len(critiques)) + " critic round(s)" if critiques else ""}
        </div>
        """, unsafe_allow_html=True)

    # Stats row
    word_count = len(report.split())
    sources    = extract_sources(report)   # Feature D — count URLs
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-chip">Topic: <span>{topic_s[:40]}</span></div>
        <div class="stat-chip">Words: <span>{word_count:,}</span></div>
        <div class="stat-chip">Sources: <span>{len(sources)}</span></div>
        <div class="stat-chip">Critic rounds: <span>{len(critiques)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ── EXPORT BUTTONS ────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        # Markdown download — same as before
        st.download_button(
            label="Download .md",
            data=report,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
        )

    with col_b:
        # Feature C — PDF download
        # generate_pdf() returns bytes, which st.download_button
        # accepts directly. The PDF is generated in memory —
        # never saved to disk, just handed to the browser.
        try:
            pdf_bytes = generate_pdf(
                topic=topic_s,
                report=report,
                critiques=critiques if critiques else None,
            )
            pdf_filename = filename.replace(".md", ".pdf")
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.button(f"PDF error: {str(e)[:30]}", disabled=True, use_container_width=True)

    with col_c:
        if st.button("Clear & start over", use_container_width=True):
            for key, val in defaults.items():
                st.session_state[key] = val
            st.rerun()

    # ── TABS ──────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Report",
        f"🔗 Sources ({len(sources)})",          # Feature D
        f"🔍 Critic ({len(critiques)} rounds)",
        "💬 Follow-up chat",
    ])

    # ── TAB 1: REPORT ─────────────────────────────────────
    with tab1:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="report-header">
            <div class="report-title">{topic_s}</div>
            <div class="report-meta">Generated {ts}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(report)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: SOURCE CARDS (Feature D) ───────────────────
    # What are source cards?
    # We scan the report text for URLs using regex,
    # then display each one as a styled clickable card.
    # This makes the sources visible and transparent.
    with tab2:
        st.markdown("""
        <div style="font-size:0.875rem;color:#6b6b80;margin-bottom:1.25rem;line-height:1.6">
            All web sources referenced in this report.
            Click any card to open the original article.
        </div>
        """, unsafe_allow_html=True)
        render_source_cards(sources)

    # ── TAB 3: CRITIC PROCESS ─────────────────────────────
    with tab3:
        if not critiques:
            st.markdown('<div style="color:#6b6b80;font-size:0.9rem;padding:1rem 0">Critic was disabled for this run.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.875rem;color:#6b6b80;margin-bottom:1.25rem">What the critic agent found in each round before revision.</div>', unsafe_allow_html=True)
            for i, critique in enumerate(critiques, 1):
                st.markdown(f"""
                <div class="critique-box">
                    <div class="critique-label">Critic feedback — round {i}</div>
                    <div class="critique-text">{critique.replace(chr(10), '<br>')}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 4: FOLLOW-UP CHAT (Feature 6) ─────────────────
    with tab4:
        st.markdown('<div style="font-size:0.875rem;color:#6b6b80;margin-bottom:1rem">Ask follow-up questions — answers are grounded in the report.</div>', unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask a follow-up question about the report...")

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = chat_with_report(
                        user_message=user_input,
                        report=report,
                        topic=topic_s,
                        chat_history=st.session_state.chat_history[:-1],
                    )
                st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})