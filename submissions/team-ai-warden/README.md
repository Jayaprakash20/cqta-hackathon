## Project Title
AI Warden

## Participant(s)
- Sameeha Shaik
- Karanbir Singh Brar
- Atharva Sanjay Kimbahune
- Tithi Patel
- Harish Senthil Kumar
- Jayaprakash Kumar

## Problem Statement
AI "resolver" agents that decide their own next step are powerful but unreliable — mid-task
they can hallucinate facts, exceed policy, or skip required steps. Teams need a faster feedback
loop that catches these quality risks the moment they happen, not after a bad action reaches the
customer.

## Solution Summary
A lightweight **orchestrator** that supervises a resolver agent step by step against a Standard
Operating Procedure (SOP) and a verified ground-truth record. After every step it flags drift —
hallucination, policy violation, or a skipped step — proposes a correction, and routes it through
a **human-in-the-loop** approval before the ticket is resolved. This shortens the quality feedback
loop from "after the mistake" to "at every step." (Shown in the demo UI as
*AI Warden · Agent Orchestrator*.)

## Tech Stack
- Python 3.11+
- Streamlit (single-page UI)
- scikit-learn — TF-IDF + LogisticRegression (the classifier agent)
- Google Gemini via `google-genai` (the orchestrator's live reasoning)
- pandas, numpy, plotly, python-dotenv

## Repository Contents
- `app.py` — single-page Streamlit app: the orchestrator demo + step-through flow
- `orchestrator.py` — classifier agent + live Gemini step-evaluation (with deterministic fallback)
- `scenario.py` — the billing case: customer record, SOP, policy, and the scripted resolver steps
- `model.py` / `data.py` — the classifier agent and its seeded synthetic training data
- `style.py` — UI styling + HTML render helpers
- `config.py` — model id, API-key env-var name, versions
- `.streamlit/config.toml` — light theme
- `requirements.txt` — dependencies

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your API key (a **Google Gemini** key):
   ```bash
   cp .env.example .env        # then edit .env and set API_KEY=<your Gemini key>
   ```
3. Run the app:
   ```bash
   streamlit run app.py        # http://localhost:8501  (add --server.port 8531 to change port)
   ```
   Tests: there is no automated test suite. Verify with `python -m py_compile *.py` (syntax) and
   `python app.py` (runs the orchestration in "bare mode"; exit code 0 means no runtime errors).
   Without a valid key the orchestrator falls back to deterministic verdicts, so the demo still runs.

## Demo
1. The ticket *"My bill is almost double this month"* is auto-classified to **Billing**.
2. Click **Run next step** — the resolver works the ticket; the orchestrator marks steps 1–4 **ON TRACK**.
3. At **step 5** the orchestrator catches a **DRIFT**: the resolver calls a valid roaming charge a
   "system error", proposes a refund over the $50 policy cap, and skips customer confirmation.
4. **Approve the correction** (human-in-the-loop).
5. The resolver gets back on track, confirms with the customer, and resolves the ticket within policy.
- Demo video: _add link here_
