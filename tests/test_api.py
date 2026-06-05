from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_flags_suspicious_numeric_and_citation_claims():
    response = client.post(
        "/analyze",
        json={
            "text": (
                "According to researchers, the tool improved accuracy by 43% for "
                "2 million users and saved $12 million. It is guaranteed to work, "
                "though it might fail in edge cases."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "suspicious"
    fired_ids = {check["id"] for check in body["fired_checks"]}
    assert "citation_without_locator" in fired_ids
    assert "confident_uncertainty_mix" in fired_ids


def test_analyze_returns_clean_for_plain_supported_text():
    response = client.post(
        "/analyze",
        json={"text": "The answer explains the tradeoff and links to https://example.com/report."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "clean"
    assert body["fired_checks"] == []
