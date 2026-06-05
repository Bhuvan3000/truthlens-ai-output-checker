
# TruthLens Trust API

A small FastAPI service that accepts AI-generated text and returns a structured trust verdict.

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

# truthlens-ai-output-checker

