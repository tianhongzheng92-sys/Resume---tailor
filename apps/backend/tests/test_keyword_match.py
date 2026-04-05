"""Tests for JD keyword normalization, synonym matching, and match scoring."""

from app.services.refiner import (
    calculate_keyword_match,
    normalize_job_keywords,
    resume_matches_jd_keyword,
)


def test_normalize_job_keywords_dedupes_across_lists() -> None:
    raw = {
        "required_skills": ["Python", "python"],
        "preferred_skills": ["Python", "AWS"],
        "keywords": ["aws", "Docker"],
    }
    n = normalize_job_keywords(raw)
    assert n["required_skills"] == ["Python"]
    assert n["preferred_skills"] == ["AWS"]
    assert n["keywords"] == ["Docker"]


def test_normalize_job_keywords_drops_long_prose() -> None:
    long_line = "x" * 100
    raw = {
        "required_skills": ["Go", long_line],
        "preferred_skills": [],
        "keywords": [],
    }
    n = normalize_job_keywords(raw)
    assert n["required_skills"] == ["Go"]


def test_resume_matches_jd_keyword_k8s_synonym() -> None:
    text = "operated production k8s clusters"
    assert resume_matches_jd_keyword("Kubernetes", text)
    assert resume_matches_jd_keyword("k8s", text)


def test_resume_matches_jd_keyword_aws_synonym() -> None:
    text = "deployed services on aws"
    assert resume_matches_jd_keyword("Amazon Web Services", text)


def test_calculate_keyword_match_counts_synonym() -> None:
    resume = {
        "summary": "Shipped features on aws and k8s",
        "workExperience": [],
        "education": [],
        "personalProjects": [],
        "additional": {
            "technicalSkills": [],
            "languages": [],
            "certificationsTraining": [],
            "awards": [],
        },
        "customSections": {},
    }
    jd = {
        "required_skills": ["Amazon Web Services", "Kubernetes"],
        "preferred_skills": [],
        "keywords": [],
    }
    assert calculate_keyword_match(resume, jd) == 100.0
