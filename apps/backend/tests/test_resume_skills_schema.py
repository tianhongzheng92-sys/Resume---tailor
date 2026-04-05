"""ResumeData skills hoisting and technicalSkills delimiter parsing."""

from app.schemas import ResumeData


def test_hoists_root_skills_into_additional() -> None:
    raw = {
        "personalInfo": {"name": "Ada"},
        "skills": ["Go", "Rust"],
        "additional": {},
    }
    m = ResumeData.model_validate(raw)
    assert m.additional.technicalSkills == ["Go", "Rust"]


def test_splits_comma_separated_technical_skills_string() -> None:
    raw = {
        "additional": {"technicalSkills": "Python, JavaScript, AWS"},
    }
    m = ResumeData.model_validate(raw)
    assert m.additional.technicalSkills == ["Python", "JavaScript", "AWS"]


def test_merges_custom_section_stringlist_skills() -> None:
    raw = {
        "additional": {"technicalSkills": ["Python"]},
        "customSections": {
            "skills": {"sectionType": "stringList", "strings": ["Docker", "K8s"]},
        },
    }
    m = ResumeData.model_validate(raw)
    assert m.additional.technicalSkills == ["Python", "Docker", "K8s"]


def test_skips_soft_skills_custom_section_name() -> None:
    raw = {
        "additional": {},
        "customSections": {
            "soft_skills": {
                "sectionType": "stringList",
                "strings": ["Communication"],
            },
        },
    }
    m = ResumeData.model_validate(raw)
    assert m.additional.technicalSkills == []
