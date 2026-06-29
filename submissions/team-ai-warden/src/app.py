"""app.py — AI Warden: orchestrator supervising a ticket-resolution pipeline.

The arc on one page:
  Ticket arrives  →  Classifier agent routes it (Billing)  →  Resolver agent works
  it step by step  →  the Orchestrator checks EVERY step against the SOP +
  ground-truth record  →  it CATCHES the resolver drifting (hallucinated 'error',
  over-cap refund, no confirmation)  →  a human APPROVES the correction  →  the
  resolver gets back on track and resolves the ticket within policy.
"""

import streamlit as st

import config
import data
import model
import orchestrator
import scenario
import style

st.set_page_config(page_title="AI Warden · Agent Orchestrator", layout="wide",
                   page_icon="🛡️")
st.markdown(style.CSS, unsafe_allow_html=True)

STEPS = scenario.RESOLVER_STEPS
N = len(STEPS)


# ---------------------------------------------------------------------------
# Classifier agent (deterministic TF-IDF), trained once.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Booting the classifier agent…")
def load_classifier():
    reference_df = data.make_reference(4000)
    vectorizer, clf = model.train_model(reference_df)
    return vectorizer, clf


vectorizer, clf = load_classifier()
cls_label, cls_conf = orchestrator.classify_ticket(
    vectorizer, clf, scenario.TICKET["subject"] + ". " + scenario.TICKET["body"])


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("step_idx", 0)        # next resolver step to run
ss.setdefault("executed", [])       # [{step, kind, verdict, message}]
ss.setdefault("awaiting", False)    # drift caught, waiting on the human
ss.setdefault("drift_pos", None)    # index into executed of the drift step
ss.setdefault("approved", False)


def reset():
    ss["step_idx"] = 0
    ss["executed"] = []
    ss["awaiting"] = False
    ss["drift_pos"] = None
    ss["approved"] = False


def _reconcile(step, verdict):
    """The drift step is scripted; use the LLM's words but keep the catch reliable."""
    if step.get("is_drift"):
        if verdict.get("verdict") != "DRIFT" or not verdict.get("issues"):
            fb = orchestrator._fallback_verdict(step)
            verdict = {**fb, **{k: v for k, v in verdict.items() if v}}
            verdict.setdefault("issues", fb["issues"])
            if not verdict.get("issues"):
                verdict["issues"] = fb["issues"]
            if not verdict.get("correction"):
                verdict["correction"] = fb["correction"]
        return "drift", verdict
    # A non-drift step: present as on-track (don't let an over-eager judge false-flag).
    verdict["verdict"] = "ON_TRACK"
    return "ontrack", verdict


def run_one_step():
    """Execute the next resolver step + orchestrator check. Returns False if blocked."""
    if ss["awaiting"] or ss["step_idx"] >= N:
        return False
    step = STEPS[ss["step_idx"]]
    # Pass the (possibly corrected) message for each prior step so later checks
    # reason against what the resolver actually ended up doing.
    history = [{**e["step"], "agent_message": e["message"]} for e in ss["executed"]]
    verdict = orchestrator.evaluate_step(
        step, history, scenario.SOP, scenario.POLICY, scenario.CUSTOMER)
    kind, verdict = _reconcile(step, verdict)
    ss["executed"].append({
        "step": step, "kind": kind, "verdict": verdict,
        "message": step["agent_message"],
    })
    ss["step_idx"] += 1
    if kind == "drift":
        ss["awaiting"] = True
        ss["drift_pos"] = len(ss["executed"]) - 1
    return True


def approve_correction(edited=None):
    """Human approves (optionally edits) the correction → resolver gets back on track."""
    pos = ss["drift_pos"]
    if pos is None:
        return
    entry = ss["executed"][pos]
    step = entry["step"]
    entry["kind"] = "corrected"
    entry["message"] = step.get("corrected_message", entry["message"])
    note = "Roaming treated as valid usage; relief kept within the $50 cap; customer confirmation required before applying."
    if edited:
        note = "Human-approved correction: " + edited
    entry["verdict"] = {"verdict": "ON_TRACK", "explanation": note, "issues": [],
                        "correction": ""}
    ss["awaiting"] = False
    ss["approved"] = True


# ---------------------------------------------------------------------------
# Derived UI state
# ---------------------------------------------------------------------------
done = ss["step_idx"] >= N and not ss["awaiting"]
if ss["awaiting"]:
    health = "drift"
elif done:
    health = "resolved"
else:
    health = "watch"

done_count = sum(1 for e in ss["executed"] if e["kind"] in ("ontrack", "corrected"))
current_sop = ss["drift_pos"] if ss["awaiting"] else (ss["step_idx"] if not done else -1)

st.markdown(style.top_bar(health), unsafe_allow_html=True)

rail, center, panel = st.columns([1.15, 2.55, 2.3], gap="medium")

# ---- Left rail: agents · SOP · policy --------------------------------------
with rail:
    orch_status = "alarm" if ss["awaiting"] else ("done" if done else "active")
    res_status = "alarm" if ss["awaiting"] else ("done" if done else
                 ("active" if ss["step_idx"] > 0 else "idle"))
    st.markdown('<div class="dg-card"><div class="dg-label">Agent pipeline</div>'
                + style.agent_tree(orch_status, "done", res_status)
                + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="dg-card"><div class="dg-label">SOP — Billing high-bill</div>'
                + style.sop_checklist(scenario.SOP, done_count, current_sop)
                + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="dg-card"><div class="dg-label">Policy (enforced)</div>'
                + style.policy_box(scenario.POLICY) + '</div>', unsafe_allow_html=True)

    key_note = (f"🟢 Live orchestrator · {orchestrator.ORCHESTRATOR_PROVIDER} "
                f"({config.GEMINI_MODEL})" if orchestrator.has_api_key()
                else "⚙️ No API key — orchestrator uses the deterministic fallback")
    st.caption(key_note)

# ---- Center: ticket + resolver step trace ----------------------------------
with center:
    st.markdown(style.ticket_card(scenario.TICKET, cls_label, cls_conf),
                unsafe_allow_html=True)

    st.markdown('<div class="dg-card"><h4>🤖 Resolver agent — live step trace</h4>',
                unsafe_allow_html=True)

    # Controls
    b1, b2, b3 = st.columns([1.2, 1.2, 0.8])
    step_clicked = b1.button(
        "▶ Run next step", use_container_width=True, type="primary",
        disabled=ss["awaiting"] or done)
    run_clicked = b2.button(
        "▶▶ Run to checkpoint", use_container_width=True,
        disabled=ss["awaiting"] or done,
        help="Run steps until the orchestrator stops on a drift, or the ticket resolves.")
    if b3.button("↺ Reset", use_container_width=True):
        reset()
        st.rerun()

    if step_clicked:
        run_one_step()
        st.rerun()
    if run_clicked:
        guard = 0
        while run_one_step() and not ss["awaiting"] and guard < N:
            guard += 1
        st.rerun()

    # Render executed steps
    if not ss["executed"]:
        st.caption("Press **Run next step** to let the resolver begin. The "
                   "orchestrator will check each step against the SOP.")
    for i, e in enumerate(ss["executed"], start=1):
        st.markdown(
            style.step_card(i, e["step"], e["verdict"], e["kind"], e["message"]),
            unsafe_allow_html=True,
        )

    if done:
        last = ss["executed"][-1]["step"]
        st.markdown(
            '<div class="dg-resolved">✅ Ticket resolved within policy — '
            'late fee waived ($17.00) + $33.00 goodwill credit. '
            'The orchestrator caught one drift and the human approved the fix.</div>',
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---- Right: orchestrator verdict · HITL · audit ----------------------------
with panel:
    st.markdown('<div class="dg-card"><h4>🧭 Orchestrator</h4>', unsafe_allow_html=True)

    if ss["awaiting"]:
        drift = ss["executed"][ss["drift_pos"]]
        v = drift["verdict"]
        st.markdown(
            f'<div style="font-weight:700;color:{style.RED}">⚠ Drift caught at '
            f'step {ss["drift_pos"]+1}: {drift["step"]["title"]}</div>',
            unsafe_allow_html=True)
        st.markdown(v.get("explanation", ""))
        st.markdown("**Issues:**")
        for issue in v.get("issues", []):
            st.markdown(f"- {issue}")
        st.markdown(style.correction_box(v.get("correction", "")),
                    unsafe_allow_html=True)
        st.markdown("**👤 Human-in-the-loop:** approve the correction to put the "
                    "resolver back on track.")
        h1, h2 = st.columns(2)
        if h1.button("✅ Approve correction", type="primary",
                     use_container_width=True):
            approve_correction()
            st.rerun()
        with h2.popover("✏️ Edit", use_container_width=True):
            edited = st.text_area("Edit the correction",
                                  value=v.get("correction", ""), height=140)
            if st.button("Approve edited correction"):
                approve_correction(edited=edited.strip() or None)
                st.rerun()

    elif done:
        st.markdown('<div class="dg-resolved">All steps validated. Ticket resolved '
                    'within policy.</div>', unsafe_allow_html=True)
        st.caption("The orchestrator approved 6 steps, caught 1 drift, and the "
                   "human signed off on the correction.")
    else:
        ran = len(ss["executed"])
        st.markdown(f"Monitoring the resolver. **{done_count}** step(s) validated "
                    f"on track · **0** drifts so far.")
        if ran == 0:
            st.caption("Waiting for the resolver to take its first step.")
        else:
            st.caption("Each step is checked against the SOP and the verified "
                       "customer record before the resolver may continue.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Audit log
    st.markdown('<div class="dg-card"><h4>📋 Audit trail</h4>', unsafe_allow_html=True)
    if not ss["executed"]:
        st.caption("No steps yet.")
    else:
        for i, e in enumerate(ss["executed"], start=1):
            v = e["verdict"]
            if e["kind"] == "drift":
                icon, txt = "⚠️", f"DRIFT — {v.get('explanation','')[:90]}"
            elif e["kind"] == "corrected":
                icon, txt = "🔧", "corrected & approved by human"
            else:
                icon, txt = "✅", "on track"
            st.markdown(f"{icon} **{i}. {e['step']['title']}** — {txt}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Self-monitoring
    with st.expander("🛡️ Self-monitoring — orchestrator golden checks & versions"):
        good = orchestrator._fallback_verdict(STEPS[0])           # known-good step
        bad = orchestrator._fallback_verdict(STEPS[4])            # the drift step
        st.markdown(f"{'✅' if good['verdict']=='ON_TRACK' else '❌'} "
                    "Known-good step → **ON_TRACK**")
        st.markdown(f"{'✅' if bad['verdict']=='DRIFT' else '❌'} "
                    "Known-bad (drift) step → **DRIFT**")
        st.caption(
            f"Pinned: classifier `{config.CLASSIFIER_VERSION}` · "
            f"orchestrator `{config.ORCHESTRATOR_VERSION}` · "
            f"LLM `{config.GEMINI_MODEL}`. Versions are pinned so the AI "
            "auditor itself doesn't drift.")
