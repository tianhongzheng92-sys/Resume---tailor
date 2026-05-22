"""Cover letter, outreach message, and resume title generation service."""

import json
from typing import Any

from app.llm import complete
from app.prompts.templates import (
    COVER_LETTER_PROMPT,
    GENERATE_TITLE_PROMPT,
    GENERATE_TITLE_ROLE_ONLY_PROMPT,
    OUTREACH_MESSAGE_PROMPT,
)
from app.prompts import get_language_name


async def generate_cover_letter(
    resume_data: dict[str, Any],
    job_description: str,
    language: str = "en",
) -> str:
    """Generate a cover letter based on resume and job description.

    Args:
        resume_data: Structured resume data (ResumeData format)
        job_description: Target job description text
        language: Output language code (en, es, zh, ja)

    Returns:
        Generated cover letter as plain text
    """
    output_language = get_language_name(language)

    prompt = COVER_LETTER_PROMPT.format(
        job_description=job_description,
        resume_data=json.dumps(resume_data, indent=2),
        output_language=output_language,
    )

    result = await complete(
        prompt=prompt,
        system_prompt="You are a professional career coach and resume writer. Write compelling, personalized cover letters.",
        max_tokens=2048,
    )

    return result.strip()


async def generate_outreach_message(
    resume_data: dict[str, Any],
    job_description: str,
    language: str = "en",
) -> str:
    """Generate a cold outreach message for networking.

    Args:
        resume_data: Structured resume data (ResumeData format)
        job_description: Target job description text
        language: Output language code (en, es, zh, ja)

    Returns:
        Generated outreach message as plain text
    """
    output_language = get_language_name(language)

    prompt = OUTREACH_MESSAGE_PROMPT.format(
        job_description=job_description,
        resume_data=json.dumps(resume_data, indent=2),
        output_language=output_language,
    )

    result = await complete(
        prompt=prompt,
        system_prompt="You are a professional networking coach. Write genuine, engaging cold outreach messages.",
        max_tokens=1024,
    )

    return result.strip()


async def generate_resume_title(
    job_description: str,
    language: str = "en",
    company_name: str | None = None,
    job_title: str | None = None,
) -> str:
    """Generate a short descriptive title from a job description.

    Args:
        job_description: Target job description text
        language: Output language code (en, es, zh, ja)
        company_name: When set, use this employer name instead of parsing from the JD
        job_title: When set, use this role title instead of parsing from the JD

    Returns:
        Generated title like "Senior Frontend Engineer @ Stripe"
    """
    registered_company = company_name.strip() if company_name else ""
    registered_title = job_title.strip() if job_title else ""

    if registered_title and registered_company:
        return f"{registered_title} @ {registered_company}"[:80]
    if registered_title:
        return registered_title[:80]

    output_language = get_language_name(language)

    if registered_company:
        prompt = GENERATE_TITLE_ROLE_ONLY_PROMPT.format(
            job_description=job_description,
            output_language=output_language,
        )
        system_prompt = (
            "You extract the hiring job title from job posts. "
            "Reply with the role title only — no company name. "
            "Never paste the employer's marketing intro."
        )
    else:
        prompt = GENERATE_TITLE_PROMPT.format(
            job_description=job_description,
            output_language=output_language,
        )
        system_prompt = (
            "You extract the hiring job title and company from job posts. "
            "Reply with one line only: 'Role @ Company' or role only. "
            "Never paste the employer's marketing intro."
        )

    result = await complete(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=60,
        temperature=0.3,
    )

    # One line only; collapse whitespace; strip quotes; cap length for DB/UI
    line = result.strip().strip("\"'").splitlines()[0].strip()
    line = " ".join(line.split())
    if registered_company:
        role = line.split("@")[0].strip() if line else ""
        if role:
            line = f"{role} @ {registered_company}"
        else:
            line = registered_company
    return line[:80] if line else ""
