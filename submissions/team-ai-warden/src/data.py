"""data.py — seeded synthetic support tickets.

Tickets are generated from per-class templates + slot vocab. Each class gets
its own distinctive vocabulary so the four TRAINED classes are linearly
separable under TF-IDF, while the NOVEL "5G Home Internet Outage" class is
built almost entirely from tokens the model never saw in training — so the
classifier is forced to be UNSURE about it (low max-proba => flagged OOD).
"""

import numpy as np
import pandas as pd

import config

# ---------------------------------------------------------------------------
# Templates per TRAINED class. {x} slots are filled from the vocab below.
# ---------------------------------------------------------------------------
TEMPLATES = {
    "Billing": [
        "I was charged twice this month for my {plan} plan",
        "My bill is way too high, there is an unexpected {fee} fee",
        "I need a refund for the {fee} charge on my invoice",
        "My payment failed but the money left my bank account",
        "I was overcharged on my latest invoice, please review",
        "Why is there a duplicate charge on my credit card statement",
        "Requesting a refund, I cancelled but was still billed",
        "There is a mistake on my invoice, the total does not add up",
        "My autopay charged the wrong amount this billing cycle",
        "Please explain these extra {fee} fees on my monthly bill",
        "I want a credit for being double billed last month",
        "The promo discount was not applied to my invoice",
    ],
    "Network": [
        "I have no mobile signal downtown since this morning",
        "My calls keep dropping in the middle of conversations",
        "Mobile data is so slow on LTE, pages will not load",
        "Poor cellular coverage at my office, only one bar",
        "My mobile data is not working at all on the highway",
        "Signal keeps dropping to 3G and then no service",
        "Cannot make phone calls, network says no service",
        "Roaming data not connecting while I travel abroad",
        "Text messages fail to send on the cellular network",
        "Terrible reception on my phone in the city center",
        "4G keeps cutting out every few minutes on my handset",
        "No bars of signal on my cell phone all day",
    ],
    "Device": [
        "My phone will not turn on even after charging overnight",
        "I need a cracked screen replacement for my handset",
        "The battery on my phone drains extremely fast now",
        "My phone will not charge with any cable I try",
        "The SIM card is not detected by my new phone",
        "My handset keeps overheating and shutting itself off",
        "The touchscreen on my phone is unresponsive",
        "My phone speaker stopped working after the last drop",
        "Camera on my device is blurry and will not focus",
        "My phone restarts randomly several times a day",
        "The charging port on my handset seems broken",
        "My device froze and now the screen is black",
    ],
    "Account": [
        "I need to reset my password, I am locked out",
        "Please update the mailing address on my account",
        "I cannot log in to my online account anymore",
        "I want to change my plan to a cheaper option",
        "Please cancel my account effective end of month",
        "How do I update the email address on my profile",
        "I forgot my username and cannot access the portal",
        "Please add my spouse as an authorized user on the account",
        "I need to update the payment method stored on my account",
        "My account got locked after too many login attempts",
        "Can you transfer my number to a new account holder",
        "I want to upgrade my membership tier on my profile",
    ],
}

# Novel class: built from tokens (home, wifi, router, hub, outage, fibre...)
# that essentially never appear in the 4 trained classes above.
NOVEL_TEMPLATES = [
    "My home internet is down and the wifi will not come back",
    "The 5G home hub is not working, no connection at all",
    "There is no wifi at home, the router shows a red light",
    "Internet outage in my area, my home broadband is dead",
    "My home router is offline and devices cannot connect",
    "The smart hub at home has no connection to the internet",
    "The whole neighbourhood internet is out since last night",
    "My 5G home receiver shows no signal and the wifi dropped",
    "Home wifi keeps disconnecting, the fibre box is blinking",
    "No home broadband, the 5G gateway will not get online",
    "My household lost internet, the wifi router is unreachable",
    "The home internet hub rebooted and now there is no wifi",
]

# ---------------------------------------------------------------------------
# Slot vocab.
# ---------------------------------------------------------------------------
VOCAB = {
    "plan": ["unlimited", "family", "prepaid", "business", "basic"],
    "fee": ["late", "service", "roaming", "activation", "overage"],
}


def _fill(rng, template):
    out = template
    for slot, options in VOCAB.items():
        token = "{" + slot + "}"
        if token in out:
            out = out.replace(token, rng.choice(options))
    return out


def _gen_for_label(rng, templates, n):
    idx = rng.integers(0, len(templates), size=n)
    return [_fill(rng, templates[i]) for i in idx]


def make_reference(n=4000):
    """Balanced labelled tickets across the 4 TRAINED classes only.

    Used to train the model and to compute the baseline class distribution.
    Returns a DataFrame with columns: text, label.
    """
    rng = np.random.default_rng(config.SEED)
    per = n // len(config.CATEGORIES)
    rows = []
    for label in config.CATEGORIES:
        for text in _gen_for_label(rng, TEMPLATES[label], per):
            rows.append({"text": text, "label": label})
    df = pd.DataFrame(rows)
    # Deterministic shuffle.
    return df.sample(frac=1.0, random_state=config.SEED).reset_index(drop=True)


def make_live(n=400, scenario="healthy", intensity=0.0):
    """A live batch of incoming tickets (text + requester).

    scenario="healthy"   -> only the 4 trained classes.
    scenario="5g_outage" -> replace up to ~40% * intensity of the batch with
                            NOVEL "5G Home Internet Outage" tickets. So
                            intensity ~0.75 yields ~30% out-of-distribution.
    """
    rng = np.random.default_rng(config.SEED + 7)  # offset so it differs from ref

    novel_count = 0
    if scenario == "5g_outage":
        novel_count = int(round(n * 0.40 * float(intensity)))
    normal_count = n - novel_count

    # Normal tickets: evenly spread across the 4 trained classes.
    normal_texts = []
    for i in range(normal_count):
        label = config.CATEGORIES[i % len(config.CATEGORIES)]
        normal_texts.append(_fill(rng, rng.choice(TEMPLATES[label])))

    novel_texts = _gen_for_label(rng, NOVEL_TEMPLATES, novel_count)

    texts = normal_texts + novel_texts
    is_novel = [False] * normal_count + [True] * novel_count

    df = pd.DataFrame({"text": texts, "is_novel": is_novel})
    # Deterministic shuffle so novel tickets are interleaved through the queue.
    df = df.sample(frac=1.0, random_state=config.SEED + 3).reset_index(drop=True)

    # Attach fake requester names deterministically.
    names = config.REQUESTER_NAMES
    df["requester"] = [names[i % len(names)] for i in range(len(df))]
    return df


def classify_one(vectorizer, clf, text):
    """Classify a single free-text ticket from the '+ New ticket' box.

    Returns (predicted_label, confidence).
    """
    from model import score  # local import avoids any import-order surprises

    scored = score(vectorizer, clf, [text])
    row = scored.iloc[0]
    return row["predicted_label"], float(row["confidence"])
