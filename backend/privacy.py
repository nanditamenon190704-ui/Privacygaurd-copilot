from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

nlp_engine = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}).create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

# Custom rules for Indian data
analyzer.registry.add_recognizer(PatternRecognizer(
    supported_entity="IN_PHONE",
    patterns=[Pattern("in_mobile", r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)", 0.6)],
))
analyzer.registry.add_recognizer(PatternRecognizer(
    supported_entity="AADHAAR",
    patterns=[Pattern("aadhaar", r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)", 0.5)],
))
# Safety net: any long run of digits is hidden, even if not a valid number
analyzer.registry.add_recognizer(PatternRecognizer(
    supported_entity="LONG_NUMBER",
    patterns=[Pattern("long_number", r"(?<!\d)\d{9,13}(?!\d)", 0.4)],
))

ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IN_PHONE",
    "AADHAAR", "LONG_NUMBER", "CREDIT_CARD", "LOCATION", "IP_ADDRESS",
]

# Friendlier names for the labels
LABELS = {"IN_PHONE": "PHONE_NUMBER", "LONG_NUMBER": "NUMBER"}


def _dedupe(findings):
    """If two detectors flag the same text, keep only the higher-scoring one."""
    kept = []
    for f in sorted(findings, key=lambda r: (-r.score, r.start)):
        if all(f.end <= k.start or f.start >= k.end for k in kept):
            kept.append(f)
    return sorted(kept, key=lambda r: r.start)


def redact(text: str) -> dict:
    """Replace personal data with numbered labels like <PERSON_1>.

    Returns the cleaned text, counts, an audit list (types and positions
    only) and a private 'mapping' of label -> real value. The mapping must
    never be sent to the AI or written to a log.
    """
    findings = _dedupe(analyzer.analyze(text=text, language="en", entities=ENTITIES))

    mapping = {}   # "<PERSON_1>" -> "Priya Nair"
    seen = {}      # ("PERSON", "Priya Nair") -> "<PERSON_1>"
    counters = {}
    counts = {}
    audit = []
    parts = []
    last = 0

    for f in findings:
        label = LABELS.get(f.entity_type, f.entity_type)
        value = text[f.start:f.end]
        key = (label, value)
        if key not in seen:
            counters[label] = counters.get(label, 0) + 1
            placeholder = f"<{label}_{counters[label]}>"
            seen[key] = placeholder
            mapping[placeholder] = value
        parts.append(text[last:f.start])
        parts.append(seen[key])
        last = f.end
        counts[label] = counts.get(label, 0) + 1
        audit.append({"type": label, "start": f.start, "end": f.end, "score": round(f.score, 2)})

    parts.append(text[last:])

    return {
        "redacted_text": "".join(parts),
        "findings": audit,
        "counts": counts,
        "mapping": mapping,
    }


def restore(text: str, mapping: dict) -> str:
    """Put the real values back into the AI's answer. Runs only on your side."""
    for placeholder, value in mapping.items():
        text = text.replace(placeholder, value)
    return text