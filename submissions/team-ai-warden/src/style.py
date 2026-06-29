"""style.py — support-desk veneer (thin CSS) + HTML render helpers.

Dark-teal top bar, white cards, an agent tree, an SOP checklist, resolver step
cards, and ON_TRACK / DRIFT verdict badges.
"""

import html as _html

# Palette
TEAL_DARK = "#03363d"
TEAL = "#37b8af"
APP_BG = "#f3f5f7"
AMBER = "#e8a33d"
BLUE = "#1f73b7"
GREEN = "#2faf6b"
RED = "#e0492f"

CSS = f"""
<style>
.stApp {{ background: {APP_BG}; color: #24323a; }}
/* Hide Streamlit's default top toolbar so our own top bar sits flush at the top */
header[data-testid="stHeader"] {{ display: none; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1550px; }}
/* Safety: keep native text dark even if the OS is in dark mode */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"], [data-testid="stExpander"] p {{ color: #24323a; }}

/* Top bar */
.dg-topbar {{
    background: {TEAL_DARK}; color: #fff; padding: 12px 20px; border-radius: 10px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}}
.dg-brand {{ font-size: 20px; font-weight: 700; letter-spacing: .3px; }}
.dg-brand .dg-dot {{ color: {TEAL}; }}
.dg-sub {{ font-size: 12px; opacity: .75; font-weight: 400; margin-left: 8px; }}
.dg-health {{ font-size: 13px; font-weight: 700; padding: 6px 14px; border-radius: 999px; }}
.dg-health.ok {{ background: rgba(47,175,107,.2); color: #c8f5dd; border: 1px solid {GREEN}; }}
.dg-health.watch {{ background: rgba(55,184,175,.18); color: #c6f3ef; border: 1px solid {TEAL}; }}
.dg-health.drift {{ background: rgba(224,73,47,.22); color: #ffd6cc; border: 1px solid {RED}; }}

/* Cards */
.dg-card {{ background: #fff; border: 1px solid #e4e8eb; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 12px; }}
.dg-card h4 {{ margin: 0 0 8px 0; font-size: 14px; color: #2b3a40; }}
.dg-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
    color: #6b7b82; font-weight: 700; margin: 6px 0 4px; }}

/* Agent tree */
.dg-agent {{ display: flex; align-items: center; gap: 8px; padding: 5px 8px;
    border-radius: 7px; font-size: 13px; color: #2b3a40; }}
.dg-agent .nm {{ font-weight: 600; }}
.dg-agent .role {{ color: #6b7b82; font-size: 11px; }}
.dg-agent.child {{ margin-left: 16px; }}
.dg-agent.gchild {{ margin-left: 32px; }}
.dg-adot {{ width: 9px; height: 9px; border-radius: 50%; flex: none; }}
.dg-adot.idle {{ background: #c2ccd0; }}
.dg-adot.active {{ background: {TEAL}; box-shadow: 0 0 0 3px rgba(55,184,175,.25); }}
.dg-adot.alarm {{ background: {RED}; box-shadow: 0 0 0 3px rgba(224,73,47,.25); }}
.dg-adot.done {{ background: {GREEN}; }}

/* SOP checklist */
.dg-sop {{ font-size: 12.5px; color: #3a4a50; line-height: 1.5; }}
.dg-sop .it {{ padding: 3px 0; }}
.dg-sop .mark {{ font-weight: 800; margin-right: 6px; }}
.dg-sop .done .mark {{ color: {GREEN}; }}
.dg-sop .cur {{ background: rgba(55,184,175,.12); border-radius: 5px; padding: 3px 6px; }}
.dg-sop .cur .mark {{ color: {TEAL}; }}

/* Ticket card */
.dg-ticket-subj {{ font-size: 15px; font-weight: 700; color: #233; }}
.dg-ticket-meta {{ font-size: 12px; color: #6b7b82; margin: 2px 0 8px; }}
.dg-ticket-body {{ font-size: 13.5px; color: #33444a; background: #f7fafa;
    border-left: 3px solid {TEAL}; padding: 8px 12px; border-radius: 6px; }}

/* Resolver step cards */
.dg-step {{ border: 1px solid #e4e8eb; border-radius: 9px; padding: 11px 13px;
    margin-bottom: 10px; background: #fff; }}
.dg-step.ontrack {{ border-left: 4px solid {GREEN}; }}
.dg-step.drift {{ border-left: 4px solid {RED}; background: #fff5f3; }}
.dg-step.corrected {{ border-left: 4px solid {TEAL}; background: #f3fbfa; }}
.dg-step.pending {{ border-left: 4px solid {AMBER}; }}
.dg-step-head {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
.dg-step-title {{ font-weight: 700; font-size: 13.5px; color: #2b3a40; }}
.dg-step-num {{ color: #9aa7ac; font-weight: 700; font-size: 12px; margin-right: 6px; }}
.dg-action {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px;
    background: #eef3f3; color: #2b6b66; border-radius: 5px; padding: 2px 7px; }}
.dg-step-msg {{ font-size: 13px; color: #33444a; margin: 7px 0 6px; }}
.dg-tool {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11.5px;
    color: #5b6b72; background: #f5f7f8; border-radius: 5px; padding: 5px 8px; }}

/* Orchestrator note under a step */
.dg-orch {{ margin-top: 8px; padding: 8px 10px; border-radius: 7px; font-size: 12.5px; }}
.dg-orch.ontrack {{ background: rgba(47,175,107,.1); color: #1d7d4b; }}
.dg-orch.drift {{ background: rgba(224,73,47,.1); color: #8a2c1c; }}
.dg-orch.corrected {{ background: rgba(55,184,175,.12); color: #1c6e69; }}
.dg-orch .oh {{ font-weight: 700; }}
.dg-orch ul {{ margin: 5px 0 0 0; padding-left: 18px; }}
.dg-orch li {{ margin: 2px 0; }}

/* Badges / pills */
.pill {{ font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 999px;
    text-transform: uppercase; letter-spacing: .03em; white-space: nowrap; }}
.pill.ontrack {{ background: rgba(47,175,107,.16); color: #1d7d4b; border: 1px solid {GREEN}; }}
.pill.drift {{ background: rgba(224,73,47,.15); color: {RED}; border: 1px solid {RED}; }}
.pill.corrected {{ background: rgba(55,184,175,.16); color: #1c6e69; border: 1px solid {TEAL}; }}
.pill.pending {{ background: rgba(232,163,61,.18); color: #a9701a; border: 1px solid {AMBER}; }}

.sev {{ font-size: 11px; font-weight: 800; padding: 2px 9px; border-radius: 5px; }}
.sev.HIGH {{ background: rgba(224,73,47,.16); color: {RED}; }}
.sev.MEDIUM {{ background: rgba(232,163,61,.2); color: #a9701a; }}
.sev.LOW {{ background: rgba(47,175,107,.16); color: #1d7d4b; }}
.sev.NONE {{ background: #eef1f3; color: #6b7b82; }}

/* Correction / HITL box */
.dg-correction {{ background: linear-gradient(135deg, {TEAL_DARK}, #0a4f57); color: #fff;
    border-radius: 9px; padding: 12px 14px; margin: 8px 0; }}
.dg-correction .cap {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em; opacity: .8; }}
.dg-correction .txt {{ font-size: 13.5px; margin-top: 4px; line-height: 1.5; }}

/* Policy box */
.dg-policy {{ font-size: 12px; color: #3a4a50; line-height: 1.55; }}
.dg-policy b {{ color: #2b3a40; }}

/* Resolution banner */
.dg-resolved {{ background: rgba(47,175,107,.12); border: 1px solid {GREEN};
    border-radius: 9px; padding: 12px 14px; color: #176c41; font-weight: 600; }}

[data-testid="stMetricValue"] {{ font-size: 24px; }}
</style>
"""


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------
def top_bar(state):
    """state ∈ {'watch', 'drift', 'resolved'}."""
    if state == "drift":
        health = '<span class="dg-health drift">● Drift caught — awaiting approval</span>'
    elif state == "resolved":
        health = '<span class="dg-health ok">● Resolved — within policy</span>'
    else:
        health = '<span class="dg-health watch">● Orchestrator monitoring</span>'
    return (
        '<div class="dg-topbar">'
        '<div><span class="dg-brand">AI Warden<span class="dg-dot">·</span> '
        'Agent Orchestrator</span>'
        '<span class="dg-sub">supervising the ticket-resolution pipeline</span></div>'
        f'{health}</div>'
    )


def _adot(status):
    return f'<span class="dg-adot {status}"></span>'


def agent_tree(orch, classifier, resolver):
    """Each arg is a status: idle | active | alarm | done."""
    return (
        f'<div class="dg-agent">{_adot(orch)}<span class="nm">Orchestrator</span>'
        f'<span class="role">· supervisor</span></div>'
        f'<div class="dg-agent child">{_adot(classifier)}'
        f'<span class="nm">Classifier agent</span><span class="role">· routes ticket</span></div>'
        f'<div class="dg-agent child">{_adot(resolver)}'
        f'<span class="nm">Resolver agent</span><span class="role">· Billing</span></div>'
    )


def sop_checklist(sop, completed_idx, current_idx):
    """completed_idx: number of SOP items done; current_idx: the active one (or -1)."""
    out = ['<div class="dg-sop">']
    for i, item in enumerate(sop):
        text = _html.escape(item)
        if i < completed_idx:
            out.append(f'<div class="it done"><span class="mark">✓</span>{text}</div>')
        elif i == current_idx:
            out.append(f'<div class="it cur"><span class="mark">▸</span>{text}</div>')
        else:
            out.append(f'<div class="it"><span class="mark" style="color:#c2ccd0">○</span>{text}</div>')
    out.append("</div>")
    return "".join(out)


def ticket_card(ticket, label, confidence):
    return (
        '<div class="dg-card">'
        f'<div class="dg-label">Ticket · classified → {_html.escape(label)} '
        f'({confidence*100:.0f}%)</div>'
        f'<div class="dg-ticket-subj">{_html.escape(ticket["subject"])}</div>'
        f'<div class="dg-ticket-meta">{_html.escape(ticket["requester"])} · '
        f'{_html.escape(ticket["channel"])}</div>'
        f'<div class="dg-ticket-body">{_html.escape(ticket["body"])}</div>'
        '</div>'
    )


def _verdict_pill(kind):
    text = {"ontrack": "● On track", "drift": "⚠ Drift", "corrected": "✓ Corrected",
            "pending": "… Reviewing"}[kind]
    return f'<span class="pill {kind}">{text}</span>'


def step_card(n, step, verdict, kind, message_override=None):
    """Render one resolver step + the orchestrator's verdict beneath it.

    kind ∈ {'ontrack', 'drift', 'corrected', 'pending'}.
    """
    msg = message_override or step["agent_message"]
    head = (
        '<div class="dg-step-head">'
        f'<div><span class="dg-step-num">STEP {n}</span>'
        f'<span class="dg-step-title">{_html.escape(step["title"])}</span></div>'
        f'{_verdict_pill(kind)}</div>'
    )
    action = f'<div style="margin:6px 0"><span class="dg-action">{_html.escape(step["action"])}()</span></div>'
    body = f'<div class="dg-step-msg">{_html.escape(msg)}</div>'
    tool = (f'<div class="dg-tool">{_html.escape(step.get("tool_result",""))}</div>'
            if step.get("tool_result") else "")

    orch = ""
    if verdict:
        if kind == "drift":
            issues = "".join(f"<li>{_html.escape(i)}</li>" for i in verdict.get("issues", []))
            sev = (verdict.get("severity") or "HIGH").upper()
            orch = (
                '<div class="dg-orch drift">'
                f'<span class="oh">Orchestrator: DRIFT </span>'
                f'<span class="sev {sev}">{sev}</span>'
                f'<div style="margin-top:4px">{_html.escape(verdict.get("explanation",""))}</div>'
                f'<ul>{issues}</ul></div>'
            )
        elif kind == "corrected":
            orch = (
                '<div class="dg-orch corrected">'
                '<span class="oh">Orchestrator: corrected step re-validated.</span> '
                f'{_html.escape(verdict.get("explanation","")) if verdict.get("explanation") else ""}</div>'
            )
        else:  # ontrack
            orch = (
                '<div class="dg-orch ontrack">'
                f'<span class="oh">Orchestrator: on track.</span> '
                f'{_html.escape(verdict.get("explanation",""))}</div>'
            )

    cls = kind if kind != "corrected" else "corrected"
    return f'<div class="dg-step {cls}">{head}{action}{body}{tool}{orch}</div>'


def correction_box(text):
    return (
        '<div class="dg-correction">'
        '<div class="cap">Orchestrator&#39;s proposed correction</div>'
        f'<div class="txt">{_html.escape(text)}</div></div>'
    )


def policy_box(policy):
    return (
        '<div class="dg-policy">'
        f'<b>Goodwill credit cap:</b> ${policy["goodwill_cap"]:.0f} '
        '(supervisor approval required above this).<br>'
        f'<b>Late-fee waiver:</b> {_html.escape(policy["late_fee_waiver"])}.<br>'
        f'<b>Valid charges:</b> {_html.escape(policy["valid_charges"])}<br>'
        f'<b>Confirmation:</b> {_html.escape(policy["confirmation"])}'
        '</div>'
    )
