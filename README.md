
# TruthLens Trust API

A small FastAPI service that accepts AI-generated text and returns a structured trust verdict.

## Submission Write-Up

### What I Built

I built a small REST API that evaluates AI-generated text for trust and review signals. The API has one endpoint, `POST /analyze`, which accepts JSON in the form:

```json
{ "text": "..." }
```

It returns a structured verdict of `clean`, `review`, or `suspicious`, along with every check result and a filtered list of only the checks that fired. Each fired check includes a short reason so the response is explainable rather than just a score.

### Key Decisions

I chose FastAPI because it is lightweight, easy to run locally, and automatically provides interactive API docs at `/docs`. I separated the HTTP layer from the checking logic so the heuristics can be tested and changed without touching the API contract.

The checks are intentionally heuristic rather than pretending to prove whether the text is true. For this kind of product, I think a useful first step is to identify claims that deserve review. I chose signals that commonly make AI answers risky:

- precise numbers without verifiable sources
- citation-like language without an actual locator
- absolute confidence mixed with uncertainty
- fresh or time-sensitive claims without a way to verify timing
- simple internal contradiction patterns

The verdict logic is also simple on purpose: no fired checks means `clean`, one low or medium issue means `review`, and either a high-severity issue or multiple medium issues means `suspicious`.

### Where AI Output Was Weak

One weak initial output was in the unsupported-statistics logic. The first version treated vague citation language, such as "according to researchers," as enough support for precise numeric claims. That was too generous because an answer can sound sourced while still giving the reader no way to verify it.

I caught this through a test case. The test sent text with multiple precise numbers and vague citation language but no URL, DOI, ISBN, or other locator. I expected the API to return `suspicious`, but it returned `review`. That showed the check was giving too much credit to source-shaped wording.

I fixed it by changing the check so precise numeric claims only count as supported when there is a verifiable locator, such as a URL, DOI, or ISBN. This made the service better aligned with the product goal: trust should depend on inspectable evidence, not just confident phrasing.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

FastAPI's interactive docs are available at `http://127.0.0.1:8000/docs`.

## Endpoint

`POST /analyze`

Request:

```json
{ "text": "According to experts, this improved accuracy by 43% for 2 million users." }
```

Response:

```json
{
  "verdict": "suspicious",
  "fired_checks": [
    {
      "id": "unsupported_specificity",
      "name": "Unsupported Specificity",
      "fired": true,
      "severity": "medium",
      "reason": "Multiple precise numeric claims appear without a URL, DOI, ISBN, or similar locator."
    },
    {
      "id": "citation_without_locator",
      "name": "Citation Without Locator",
      "fired": true,
      "severity": "medium",
      "reason": "The answer gestures at a source but gives no URL, DOI, ISBN, or other locator."
    }
  ],
  "checks": [
    {
      "id": "unsupported_specificity",
      "name": "Unsupported Specificity",
      "fired": true,
      "severity": "medium",
      "reason": "Multiple precise numeric claims appear without a URL, DOI, ISBN, or similar locator."
    },
    {
      "id": "citation_without_locator",
      "name": "Citation Without Locator",
      "fired": true,
      "severity": "medium",
      "reason": "The answer gestures at a source but gives no URL, DOI, ISBN, or other locator."
    }
  ]
}
```

`checks` contains every check result. `fired_checks` is the filtered list that needs attention.

## Checks Chosen

This service intentionally uses transparent heuristic checks rather than pretending to prove truth. The goal is to identify answers that deserve human review.

1. **Unsupported Specificity**
   AI answers often sound convincing by using exact numbers. Multiple precise claims without a URL, DOI, ISBN, or similar locator are a useful review signal because specificity can create false confidence.

2. **Citation Without Locator**
   Phrases like "according to researchers" can imply evidence while giving the reader no way to inspect it. The check fires when citation language appears without a URL, DOI, ISBN, or similar locator.

3. **Confident Uncertainty Mix**
   A risky answer may combine absolute wording such as "guaranteed" or "never" with hedges such as "might" or "possibly." That tension is not automatically false, but it is a strong signal that the claim needs a tighter explanation.

4. **Time-Sensitive Claim Without Timestamp**
   Claims using "currently," "latest," or "today" decay quickly. Without a link or timestamp-like locator, the answer may already be stale.

5. **Possible Internal Contradiction**
   The service looks for simple opposing claim patterns, such as saying there is "no evidence" while also saying "evidence shows." This is high severity because contradictions undermine trust even before external fact-checking.

## Verdicts

- `clean`: no checks fired
- `review`: one low or medium concern fired
- `suspicious`: any high-severity concern, or two or more medium concerns

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t truthlens-api .
docker run --rm -p 8000:8000 truthlens-api
```

