from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.checks import CheckResult, overall_verdict, run_checks


app = FastAPI(
    title="TruthLens Trust API",
    version="0.1.0",
    description="Scores AI-generated text for lightweight trust and review signals.",
)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="AI-generated text to evaluate.")


class CheckResponse(BaseModel):
    id: str
    name: str
    fired: bool
    severity: str
    reason: str


class AnalyzeResponse(BaseModel):
    verdict: str
    fired_checks: list[CheckResponse]
    checks: list[CheckResponse]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_text(payload: AnalyzeRequest) -> AnalyzeResponse:
    results = run_checks(payload.text)
    checks = [_to_response(result) for result in results]
    return AnalyzeResponse(
        verdict=overall_verdict(results),
        fired_checks=[check for check in checks if check.fired],
        checks=checks,
    )


def _to_response(result: CheckResult) -> CheckResponse:
    return CheckResponse(
        id=result.id,
        name=result.name,
        fired=result.fired,
        severity=result.severity.value,
        reason=result.reason,
    )
