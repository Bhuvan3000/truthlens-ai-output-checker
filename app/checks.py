import re
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class CheckResult:
    id: str
    name: str
    fired: bool
    severity: Severity
    reason: str


URL_PATTERN = re.compile(r"https?://[^\s)\]]+", re.IGNORECASE)
CITATION_PATTERN = re.compile(
    r"\b(?:according to|source:|sources:|cited by|as reported by|study by)\b",
    re.IGNORECASE,
)
NUMERIC_CLAIM_PATTERN = re.compile(
    r"(?<![\w.])(?:\d+(?:\.\d+)?%|\$?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|trillion|percent|people|users|cases|times|x|fold)?)\b",
    re.IGNORECASE,
)
ABSOLUTE_LANGUAGE_PATTERN = re.compile(
    r"\b(?:always|never|guaranteed|proves?|undeniable|certainly|no evidence|everyone|nobody|completely safe|risk-free)\b",
    re.IGNORECASE,
)
UNCERTAINTY_PATTERN = re.compile(
    r"\b(?:might|may|could|possibly|likely|appears|seems|roughly|approximately|I think|I believe|cannot verify|not sure)\b",
    re.IGNORECASE,
)
TIME_SENSITIVE_PATTERN = re.compile(
    r"\b(?:currently|today|yesterday|tomorrow|latest|newest|right now|this year|last year|as of now|recently)\b",
    re.IGNORECASE,
)
CONTRADICTION_PATTERNS = [
    (
        re.compile(r"\b(?:no|zero|not any)\s+evidence\b", re.IGNORECASE),
        re.compile(r"\bevidence\s+(?:shows|suggests|indicates|confirms)\b", re.IGNORECASE),
    ),
    (
        re.compile(r"\b(?:always|guaranteed|certainly)\b", re.IGNORECASE),
        re.compile(r"\b(?:not always|not guaranteed|uncertain|unknown|may not|might not)\b", re.IGNORECASE),
    ),
    (
        re.compile(r"\b(?:safe|risk-free|harmless)\b", re.IGNORECASE),
        re.compile(r"\b(?:dangerous|harmful|risk|unsafe)\b", re.IGNORECASE),
    ),
]


def run_checks(text: str) -> list[CheckResult]:
    normalized = " ".join(text.split())
    checks = [
        unsupported_specificity(normalized),
        citation_without_locator(normalized),
        confident_uncertainty_mix(normalized),
        time_sensitive_claim(normalized),
        contradiction_signal(normalized),
    ]
    return checks


def overall_verdict(results: list[CheckResult]) -> str:
    fired = [result for result in results if result.fired]
    high_count = sum(result.severity == Severity.HIGH for result in fired)
    medium_count = sum(result.severity == Severity.MEDIUM for result in fired)

    if high_count or medium_count >= 2:
        return "suspicious"
    if fired:
        return "review"
    return "clean"


def unsupported_specificity(text: str) -> CheckResult:
    numbers = NUMERIC_CLAIM_PATTERN.findall(text)
    has_support = bool(URL_PATTERN.search(text) or re.search(r"\bdoi:\s*\S+|\bISBN\b", text, re.IGNORECASE))
    fired = len(numbers) >= 2 and not has_support
    return CheckResult(
        id="unsupported_specificity",
        name="Unsupported Specificity",
        fired=fired,
        severity=Severity.MEDIUM,
        reason=(
            "Multiple precise numeric claims appear without a URL, DOI, ISBN, or similar locator."
            if fired
            else "No cluster of unsupported precise numeric claims was found."
        ),
    )


def citation_without_locator(text: str) -> CheckResult:
    mentions_citation = bool(CITATION_PATTERN.search(text))
    has_locator = bool(URL_PATTERN.search(text) or re.search(r"\bdoi:\s*\S+|\bISBN\b", text, re.IGNORECASE))
    fired = mentions_citation and not has_locator
    return CheckResult(
        id="citation_without_locator",
        name="Citation Without Locator",
        fired=fired,
        severity=Severity.MEDIUM,
        reason=(
            "The answer gestures at a source but gives no URL, DOI, ISBN, or other locator."
            if fired
            else "Citation language, when present, includes enough locator detail or is absent."
        ),
    )


def confident_uncertainty_mix(text: str) -> CheckResult:
    confident_terms = set(match.group(0).lower() for match in ABSOLUTE_LANGUAGE_PATTERN.finditer(text))
    uncertainty_terms = set(match.group(0).lower() for match in UNCERTAINTY_PATTERN.finditer(text))
    fired = bool(confident_terms and uncertainty_terms)
    return CheckResult(
        id="confident_uncertainty_mix",
        name="Confident Uncertainty Mix",
        fired=fired,
        severity=Severity.LOW,
        reason=(
            "The answer combines absolute wording with uncertainty language, which can mask weak support."
            if fired
            else "The answer does not mix strong certainty claims with uncertainty markers."
        ),
    )


def time_sensitive_claim(text: str) -> CheckResult:
    has_time_sensitive_language = bool(TIME_SENSITIVE_PATTERN.search(text))
    has_locator = bool(URL_PATTERN.search(text))
    fired = has_time_sensitive_language and not has_locator
    return CheckResult(
        id="time_sensitive_claim",
        name="Time-Sensitive Claim Without Timestamp",
        fired=fired,
        severity=Severity.LOW,
        reason=(
            "The answer makes a fresh or relative-time claim without a link that could verify when it was true."
            if fired
            else "No unsupported fresh or relative-time claim was detected."
        ),
    )


def contradiction_signal(text: str) -> CheckResult:
    fired = any(left.search(text) and right.search(text) for left, right in CONTRADICTION_PATTERNS)
    return CheckResult(
        id="possible_internal_contradiction",
        name="Possible Internal Contradiction",
        fired=fired,
        severity=Severity.HIGH,
        reason=(
            "Opposing claim patterns appear in the same answer and should be reconciled manually."
            if fired
            else "No simple opposing claim patterns were found."
        ),
    )
