"""orchestrator.py — the Orchestrator (supervisor) + Classifier agents.

- classify_ticket(): the Classifier agent routes the ticket to a category
  (deterministic TF-IDF model — reused from the classifier work).
- evaluate_step(): the Orchestrator agent — the ONE live reasoning surface.
  Given the SOP, the ground-truth customer record, the steps so far, and the
  Resolver's PROPOSED next step, it decides ON_TRACK vs DRIFT and, on drift,
  lists the specific issues and a concrete correction.

Every call has a deterministic fallback (derived from the scripted scenario) so
the demo never hard-crashes if the Anthropic call is unavailable.
"""

import json
import os
import time

from dotenv import load_dotenv

import config
from model import score

load_dotenv()  # pulls API_KEY out of .env


def api_key():
    return os.getenv(config.API_KEY_ENV)


def has_api_key():
    return bool(api_key())


# ---------------------------------------------------------------------------
# Classifier agent
# ---------------------------------------------------------------------------
def classify_ticket(vectorizer, clf, text):
    """Route a ticket to a category. Returns (label, confidence)."""
    scored = score(vectorizer, clf, [text])
    row = scored.iloc[0]
    return row["predicted_label"], float(row["confidence"])


# ---------------------------------------------------------------------------
# Orchestrator agent — evaluate one resolver step
# ---------------------------------------------------------------------------
ORCHESTRATOR_PROVIDER = "Google Gemini"

SYSTEM_PROMPT = (
    "You are the ORCHESTRATOR — a senior QA supervisor agent overseeing a "
    "front-line support RESOLVER agent that resolves customer tickets step by "
    "step. The resolver decides its own next action, so it can hallucinate, skip "
    "a required step, or violate policy. You are given: the Standard Operating "
    "Procedure (SOP), the company policy, the VERIFIED ground-truth customer "
    "record, the steps taken so far, and the resolver's PROPOSED next step. "
    "Decide whether the proposed step is ON_TRACK or a DRIFT. A DRIFT is any of: "
    "a hallucination (a claim that contradicts the customer record), a policy "
    "violation, a skipped/ out-of-order SOP step, an out-of-scope action, or "
    "resolving without required customer confirmation. If it drifts, name the "
    "specific issues, cite the SOP section or the data, and give a concrete "
    "correction that gets the resolver back on track. Respond with ONLY valid "
    "JSON, no markdown."
)

JSON_SHAPE = """{
  "verdict": "ON_TRACK | DRIFT",
  "severity": "NONE | LOW | MEDIUM | HIGH",
  "issues": ["each specific problem, citing the SOP section or the data"],
  "explanation": "one or two sentences: why this verdict",
  "correction": "if DRIFT, the concrete corrected action; else empty string"
}"""


def _strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    return t.strip()


def _fallback_verdict(step):
    """Deterministic verdict derived from the scripted scenario."""
    if step.get("is_drift"):
        return {
            "verdict": "DRIFT",
            "severity": "HIGH",
            "issues": list(step.get("drift_reasons", [])),
            "explanation": (
                "The proposed step contradicts the customer record and company "
                "policy and skips required confirmation."
            ),
            "correction": step.get("correction", ""),
            "_fallback": True,
        }
    return {
        "verdict": "ON_TRACK",
        "severity": "NONE",
        "issues": [],
        "explanation": step.get("note", "Step follows the SOP."),
        "correction": "",
        "_fallback": True,
    }


def _build_user_msg(sop, policy, customer, history, step):
    payload = {
        "sop": sop,
        "policy": policy,
        "verified_customer_record": customer,
        "steps_taken_so_far": [
            {"title": h["title"], "action": h["action"], "output": h["agent_message"]}
            for h in history
        ],
        "resolver_proposed_next_step": {
            "title": step["title"],
            "action": step["action"],
            "output": step["agent_message"],
            "data_pulled": step.get("tool_result", ""),
            "sop_reference": step.get("sop_ref", ""),
        },
    }
    return (
        "Evaluate the resolver's PROPOSED next step against the SOP, the policy, "
        "and the verified customer record.\n\n"
        + json.dumps(payload, indent=2)
        + "\n\nRespond with ONLY a JSON object in EXACTLY this shape:\n"
        + JSON_SHAPE
    )


def evaluate_step(step, history, sop, policy, customer):
    """Orchestrator judgment for one resolver step. Returns a verdict dict.

    Falls back to a deterministic verdict on ANY API failure so the demo is safe.
    """
    last_exc = None
    for attempt in range(2):
        try:
            from google import genai
            from google.genai import types

            key = api_key()
            if not key:
                raise RuntimeError("no API key set")

            client = genai.Client(api_key=key)
            cfg_kwargs = dict(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=config.LLM_MAX_TOKENS,
                response_mime_type="application/json",
            )
            # 2.5-series models think by default and would eat the token budget;
            # disable it for fast, reliable JSON verdicts. (No-op flag on 2.0.)
            if "2.5" in config.GEMINI_MODEL:
                cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            resp = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=_build_user_msg(sop, policy, customer, history, step),
                config=types.GenerateContentConfig(**cfg_kwargs),
            )
            text = resp.text
            if not text:
                raise RuntimeError("empty response from Gemini")
            parsed = json.loads(_strip_fences(text))
            # Defensive merge so the UI never KeyErrors.
            result = {**_fallback_verdict(step), **parsed}
            result["_fallback"] = False
            # Normalize.
            result["verdict"] = "DRIFT" if str(result.get("verdict", "")).upper().startswith("D") else "ON_TRACK"
            if not isinstance(result.get("issues"), list):
                result["issues"] = [str(result.get("issues", ""))] if result.get("issues") else []
            return result
        except Exception as exc:  # noqa: BLE001 — demo must never crash on the API
            last_exc = exc
            msg = str(exc)
            # Rate-limited: the retry delay is 30s+, too long for a live demo —
            # fall back immediately. Transient overload (503): one quick retry.
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                break
            if attempt == 0:
                time.sleep(1.5)
    print(f"[AI Warden] orchestrator fell back to scripted verdict: {last_exc}")
    return _fallback_verdict(step)
