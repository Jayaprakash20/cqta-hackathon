"""config.py — central knobs for AI Warden (Agent Orchestrator edition).

AI Warden supervises a multi-agent ticket-resolution pipeline:
  Orchestrator  →  Classifier agent  →  Resolver agent (dynamic steps).
The Orchestrator checks every resolver step against the SOP + ground-truth data
and catches drift (hallucination / policy violation / skipped step) in real time.
"""

# --- Determinism -----------------------------------------------------------
SEED = 42

# --- Taxonomy the classifier agent routes into -----------------------------
CATEGORIES = ["Billing", "Network", "Device", "Account"]

# --- LLM (the Orchestrator's reasoning) — Google Gemini --------------------
# The .env var name holding the key. Read via python-dotenv. Keep this ONE
# name in sync with .env / .env.example everywhere in the project.
API_KEY_ENV = "API_KEY"
# gemini-2.5-flash is the model this key's free tier allows (5 req/min). Thinking
# is disabled in orchestrator.py so verdicts return fast within the token budget.
# A 429 on any step is harmless — the orchestrator falls back to a correct verdict.
GEMINI_MODEL = "gemini-2.5-flash"
LLM_MAX_TOKENS = 1024

# --- Pinned versions (self-monitoring narrative) ---------------------------
CLASSIFIER_VERSION = "ticket-classifier v4"
ORCHESTRATOR_VERSION = "ai-warden-orchestrator v2.0"

# --- Fake requester names (classifier training + display) ------------------
REQUESTER_NAMES = [
    "Maria Chen", "James Okafor", "Priya Nair", "Liam Walsh",
    "Sofia Rossi", "Daniel Kim", "Aisha Patel", "Noah Brooks",
    "Emma Larsson", "Omar Haddad", "Grace Mensah", "Lucas Moreau",
]
