"""LLM prompt templates for resume processing."""

# Language code to full name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "pt": "Brazilian Portuguese",
}


def get_language_name(code: str) -> str:
    """Get full language name from code."""
    return LANGUAGE_NAMES.get(code, "English")


# Schema with example values - used for prompts to show LLM expected format
RESUME_SCHEMA_EXAMPLE = """{
  "personalInfo": {
    "name": "John Doe",
    "title": "Software Engineer",
    "email": "john@example.com",
    "phone": "+1-555-0100",
    "location": "San Francisco, CA",
    "website": "https://johndoe.dev",
    "linkedin": "linkedin.com/in/johndoe",
    "github": "github.com/johndoe"
  },
  "summary": "Experienced software engineer with 5+ years...",
  "workExperience": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "years": "Jan 2020 - Present",
      "description": [
        "Led development of microservices architecture",
        "Improved system performance by 40%"
      ]
    }
  ],
  "education": [
    {
      "id": 1,
      "institution": "University of California",
      "degree": "B.S. Computer Science",
      "years": "2014 - 2018",
      "description": "Graduated with honors"
    }
  ],
  "personalProjects": [
    {
      "id": 1,
      "name": "Open Source Tool",
      "role": "Creator & Maintainer",
      "years": "Mar 2021 - Present",
      "description": [
        "Built CLI tool with 1000+ GitHub stars",
        "Used by 50+ companies worldwide"
      ]
    }
  ],
  "additional": {
    "technicalSkills": ["Python", "JavaScript", "AWS", "Docker"],
    "languages": ["English (Native)", "Spanish (Conversational)"],
    "certificationsTraining": ["AWS Solutions Architect"],
    "awards": ["Employee of the Year 2022"]
  },
  "customSections": {
    "publications": {
      "sectionType": "itemList",
      "items": [
        {
          "id": 1,
          "title": "Paper Title",
          "subtitle": "Journal Name",
          "years": "Jun 2023",
          "description": ["Brief description of the publication"]
        }
      ]
    },
    "volunteer_work": {
      "sectionType": "text",
      "text": "Description of volunteer activities..."
    }
  }
}"""

# Schema for improve prompts - excludes personalInfo (preserved from original)
IMPROVE_SCHEMA_EXAMPLE = """{
  "summary": "Experienced software engineer with 5+ years...",
  "workExperience": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "years": "Jan 2020 - Present",
      "description": [
        "Led development of microservices architecture",
        "Improved system performance by 40%"
      ]
    }
  ],
  "education": [
    {
      "id": 1,
      "institution": "University of California",
      "degree": "B.S. Computer Science",
      "years": "2014 - 2018",
      "description": "Graduated with honors"
    }
  ],
  "personalProjects": [
    {
      "id": 1,
      "name": "Open Source Tool",
      "role": "Creator & Maintainer",
      "years": "Mar 2021 - Present",
      "description": [
        "Built CLI tool with 1000+ GitHub stars",
        "Used by 50+ companies worldwide"
      ]
    }
  ],
  "additional": {
    "technicalSkills": ["Python", "JavaScript", "AWS", "Docker"],
    "languages": ["English (Native)", "Spanish (Conversational)"],
    "certificationsTraining": ["AWS Solutions Architect"],
    "awards": ["Employee of the Year 2022"]
  },
  "customSections": {
    "publications": {
      "sectionType": "itemList",
      "items": [
        {
          "id": 1,
          "title": "Paper Title",
          "subtitle": "Journal Name",
          "years": "Jun 2023",
          "description": ["Brief description of the publication"]
        }
      ]
    },
    "volunteer_work": {
      "sectionType": "text",
      "text": "Description of volunteer activities..."
    }
  }
}"""

# Shared framing for all improve-resume prompts. JSON-only API: no match-score prose or A/B text in the model output.
IMPROVE_RECRUITER_ATS_FRAMEWORK = """=== SENIOR RECRUITER + ATS OPTIMIZATION (INTERNAL TARGETS; JSON ONLY) ===
Act as a senior technical recruiter and ATS optimization expert.

**Output contract:** Your reply must be ONLY the JSON object matching the schema at the end. Do NOT output: a match score, "Score: X%", numbered reasons, a "Missing Keywords / Gaps" list, markdown section headers such as [Match Score] or [Version A], "---" dividers, or two separate resume versions. The app stores one tailored resume and computes keyword match in the pipeline—never duplicate that in prose.

**Alignment target (honest):** Tune wording so keyword match, skills alignment, experience relevance, and seniority fit would *typically* land in the **70–90%** range when the candidate's real background honestly supports that level of fit. If the resume and JD only partially overlap, preserve truthfulness over score; do not add skills, employers, tools, or metrics to fake alignment.

**One resume, two goals:** Produce a single JSON resume that simultaneously:
- **ATS track:** Weave important JD keywords naturally; use recognizable tool/stack spellings from the JD when they match real experience; keep lists scannable; avoid stuffing and redundant keyword repetition.
- **Recruiter track:** Keep bullets clean and concise (about 1–2 lines each); use strong, varied action verbs; lead with outcomes and impact, not generic responsibilities.

**Tailoring:** Map experience to JD responsibilities and requirements only where the source resume supports it. Prioritize impact over task lists; remove or reduce irrelevant or low-impact content where your mode rules allow. Keep values ATS-friendly plain text (no markdown tables inside strings).

**Metrics:** Where your mode allows bullet edits, aim for a high share of workExperience bullets (target **70%+**) to include a measurable result (%, $, scale, users, latency, timelines, counts, team size, etc.) only when the original resume states or clearly implies it—never invent or "estimate" metrics to hit the ratio. In minimal-edit modes, only rephrase existing facts to surface implied scale; do not fabricate numbers."""

PARSE_RESUME_PROMPT = """Parse this resume into JSON. Output ONLY the JSON object, no other text.

Map content to standard sections when possible. For non-standard sections (like Publications, Volunteer Work, Research, Hobbies), add them to customSections with an appropriate type.

Example output format:
{schema}

Custom section types:
- "text": Single text block (e.g., objective, statement)
- "itemList": List of items with title, subtitle, years, description (e.g., publications, research)
- "stringList": Simple list of strings (e.g., hobbies, interests)

Rules:
- Use "" for missing text fields, [] for missing arrays, null for optional fields
- Number IDs starting from 1
- Format dates preserving the original precision. Keep months when present: "Jan 2020 - Dec 2023", "May 2021 - Present". Use "YYYY - YYYY" only when the source has no months.
- Use snake_case for custom section keys (e.g., "volunteer_work", "publications")
- Preserve the original section name as a descriptive key
- Normalize date separators: "2020-2021" → "2020 - 2021", "Current"/"Ongoing" → "Present". Do NOT discard months.
- For ambiguous dates like "3 years experience", infer approximate years from context or use "~YYYY"
- Flag overlapping dates (concurrent roles) by preserving both, don't merge

Resume to parse:
{resume_text}"""

EXTRACT_KEYWORDS_PROMPT = """Extract job requirements as JSON. Output ONLY the JSON object, no other text.

Example format:
{{
  "required_skills": ["Python", "AWS"],
  "preferred_skills": ["Kubernetes"],
  "experience_requirements": ["5+ years"],
  "education_requirements": ["Bachelor's in CS"],
  "key_responsibilities": ["Lead team"],
  "keywords": ["microservices", "agile"],
  "experience_years": 5,
  "seniority_level": "senior"
}}

Extract numeric years (e.g., "5+ years" → 5) and infer seniority level.

Job description:
{job_description}"""

CRITICAL_TRUTHFULNESS_RULES_TEMPLATE = """CRITICAL TRUTHFULNESS RULES - NEVER VIOLATE:
1. DO NOT add any skill, tool, technology, or certification that is not explicitly mentioned in the original resume
2. DO NOT invent numeric achievements (e.g., "increased by 30%") unless they exist in original
3. DO NOT add company names, product names, or technical terms not in the original
4. DO NOT upgrade experience level (e.g., "Junior" -> "Senior")
5. DO NOT add languages, frameworks, or platforms the candidate hasn't used
6. DO NOT extend employment dates or change timelines. Copy date ranges exactly as they appear, including months.
7. {rule_7}
8. Preserve factual accuracy - only use information provided by the candidate
9. NEVER remove existing skills, certifications, languages, or awards. You may reorder by relevance, but every original item must remain.

Violation of these rules could cause serious problems for the candidate in job interviews.
"""


def _build_truthfulness_rules(rule_7: str) -> str:
    return CRITICAL_TRUTHFULNESS_RULES_TEMPLATE.format(rule_7=rule_7)


CRITICAL_TRUTHFULNESS_RULES = {
    "nudge": _build_truthfulness_rules(
        "DO NOT add new bullet points or content - only rephrase existing content"
    ),
    "keywords": _build_truthfulness_rules(
        "You may rephrase existing bullet points to include keywords, but do NOT add new bullet points"
    ),
    "full": _build_truthfulness_rules(
        "You may expand existing bullet points or add new ones that elaborate on existing work, but DO NOT invent entirely new responsibilities"
    ),
    "other": _build_truthfulness_rules(
        "You may replace or add workExperience description bullets (target 5–6 per job) only when each bullet remains grounded in the original resume: do NOT add employers, tools, certifications, or metrics the candidate did not have; map JD language to honest equivalents of their real work"
    ),
}

IMPROVE_RESUME_PROMPT_NUDGE = """Lightly nudge this resume toward the job description. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

{recruiter_ats_framework}

IMPORTANT: Generate ALL text content (summary, descriptions, skills) in {output_language}.
Do NOT include personalInfo in your output - it will be preserved from the original resume.

Rules:
- Act as a senior technical recruiter optimizing for human readers and ATS: plain strings in JSON only (no markdown tables or special formatting in field values).
- Make minimal, conservative edits only where there is a clear existing match
- Prefer outcome-oriented phrasing over pure task lists when the original bullet supports it (same facts, stronger lead).
- Do NOT change the candidate's role, industry, or seniority level
- Do NOT introduce new tools, technologies, or certifications not already present
- Do NOT add new bullet points or sections
- Preserve original bullet count and ordering within each section
- Keep proper nouns (names, company names, locations) unchanged
- For customSections: preserve exact structure, item count, titles, subtitles, and years. If an item's description is an empty array [] in the original, keep it empty []. Do NOT generate descriptions for items that had none.
- Copy the "years" field values EXACTLY as they appear in the original resume (including any month prefixes like "Jan 2020 - Present"). Do not shorten, reformat, or drop months.
- If the resume is non-technical, do NOT add technical jargon
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it
- Quantify impact (light touch): where a bullet already states or clearly implies scale, time, counts, or percentages, keep or surface that signal in plain form; do not add new numbers.
- Anti-repetition: if two adjacent bullets start with the same action verb, rephrase one opener (keep facts). Avoid repeating identical clause openings across bullets.

Job Description:
{job_description}

Keywords to emphasize (only if already supported by resume content):
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""

IMPROVE_RESUME_PROMPT_KEYWORDS = """Enhance this resume with relevant keywords from the job description. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

{recruiter_ats_framework}

IMPORTANT: Generate ALL text content (summary, descriptions, skills) in {output_language}.
Do NOT include personalInfo in your output - it will be preserved from the original resume.

Rules:
- Act as a senior technical recruiter and resume optimization expert (within the truthfulness rules above). Goal: strong alignment to the job description and ATS-friendly wording without sounding robotic.
- Strengthen alignment by weaving in relevant keywords where evidence already exists; use exact JD spellings for tools and terms when they match real experience—natural prose, not keyword stuffing or repeated filler.
- Align bullets with JD-required skills, tools, and responsibilities only where the resume supports them; emphasize recent and most relevant roles first in how you rephrase (keep section order unless reordering bullets within a role improves relevance).
- Strong, varied action verbs; avoid repeating the same opening verb across adjacent bullets.
- Anti-repetition (common “Repetition” score failure): across ALL workExperience and personalProjects bullets combined, each major opening verb (e.g. developed, built, led, designed, implemented, managed, delivered, optimized, automated, streamlined, executed, used) may appear at most twice as the first word of a bullet—use synonyms and different sentence shapes. Do not reuse the same multi-word template or clause opener across bullets unless it is a proper noun or tool name.
- Impact over duties: lead bullets with outcomes the source supports; keep each bullet concise (about one or two lines of text).
- Tighten or shorten low-relevance wording; do not delete required structure (same bullet counts per truthfulness rules).
- You may rephrase bullet points to include keyword phrasing
- Do NOT introduce new skills, tools, or certifications not in the resume
- Do NOT change role, industry, or seniority level
- For customSections: preserve exact structure, item count, titles, subtitles, and years. If an item's description is an empty array [] in the original, keep it empty []. Do NOT generate descriptions for items that had none.
- Copy the "years" field values EXACTLY as they appear in the original resume (including any month prefixes like "Jan 2020 - Present"). Do not shorten, reformat, or drop months.
- If resume is non-technical, keep language non-technical while still aligning keywords
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it
- Skills: One skill per line (vertical list, no commas). Include all JD-relevant skills the candidate is qualified for.
- Quantify impact: rewrite weaker bullets so they lead with or include concrete metrics where the resume already supports them (percentages, counts, team size, latency, savings, users, release cadence, data volume, duration). Make implicit scale explicit when it is clearly grounded in the original text. Never invent statistics; do not infer or estimate numbers to “fill in” gaps—omit metrics rather than guess.
- Aim for a high share of bullets with measurable signals when the source allows; never fabricate to hit a percentage target.

Job Description:
{job_description}

Keywords to emphasize:
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""

IMPROVE_RESUME_PROMPT_FULL = """Tailor this resume for the job. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

{recruiter_ats_framework}

IMPORTANT: Generate ALL text content (summary, descriptions, skills) in {output_language}.
Do NOT include personalInfo in your output - it will be preserved from the original resume.

Rules:
- Act as a senior technical recruiter optimizing for impact and ATS: tailored JSON resume, plain text inside string fields (no complex formatting).
- Make targeted adjustments to bullet points to align with job description phrasing. Preserve the candidate's original details and voice—adjust wording toward JD skills, tools, and responsibilities where supported.
- DO NOT invent new information
- Use strong, varied action verbs; avoid repeating the same opening verb on adjacent bullets. Do not invent quantifiable achievements not in the original.
- Anti-repetition: same global verb-cap as keyword mode—each major bullet opener at most twice across experience + projects; vary phrasing and bullet structure; no copy-paste sentence frames.
- Impact first: emphasize outcomes and measurable results where the source provides or clearly implies them ($, %, scale, performance, timelines). Never infer or estimate metrics; never keyword-stuff.
- Prioritize rewrites on the most recent and JD-relevant roles; trim or sharpen low-impact phrasing without removing required entries.
- Keep proper nouns (names, company names, locations) unchanged
- Translate job titles, descriptions, and skills to {output_language}
- For customSections: preserve exact structure, item count, titles, subtitles, and years. If an item's description is an empty array [] in the original, keep it empty []. Do NOT generate descriptions for items that had none.
- Improve custom section content the same way as standard sections
- Copy the "years" field values EXACTLY as they appear in the original resume (including any month prefixes like "Jan 2020 - Present"). Do not shorten, reformat, or drop months.
- Calculate and emphasize total relevant experience duration when it matches requirements
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it
- Quantify impact: increase recruiter-ready evidence by weaving specific numbers into bullets wherever the original resume already provides or strongly implies them (e.g. performance gains, error rates, throughput, headcount, budget, timelines, adoption). Reframe vague lines into outcome + metric when the source supports it. Do not fabricate figures; do not infer “reasonable estimates.” Missing data stays honest (scope without a fake number).
- Aim for most Experience bullets to include a measurable element when the resume can support it; never invent to reach a quota.
- Skills: keep additional.technicalSkills (and related lists) keyword-aligned for ATS—JD-relevant, candidate-qualified terms first, one skill per line, natural readability.

Job Description:
{job_description}

Keywords to emphasize:
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""




IMPROVE_RESUME_PROMPT_OTHER = """Tailor this resume for the job. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

{recruiter_ats_framework}

IMPORTANT: Generate ALL text content (summary, descriptions, skills) in {output_language}.
Do NOT include personalInfo in your output - it will be preserved from the original resume.

=== CLARITY (read this—resolves common confusion) ===
- Output format: Valid JSON matching the schema at the end only. Field workExperience[].description is an array of bullet strings (that is your "Professional Experience" body). "Plain text" means: normal sentences inside those strings—no markdown, no "---" dividers, no literal section labels like "Summary:" inside a bullet.
- JD data: Use the full Job Description below plus the extracted Keywords list for STEP 1; do not ignore them.
- Scope: Apply the same JD-alignment discipline to personalProjects when project facts support it. For customSections: preserve exact structure, item count, ids, titles, subtitles, and years; improve description text only where the original had content and facts support JD phrasing.
- Dates: Copy every workExperience (and project) "years" value EXACTLY as in the original resume (including months). Do not shorten or reformat.
- Metrics: Keep every number, percentage, and metric from the source resume. You may rephrase around them; do not invent new statistics. Do not infer or estimate metrics “for realism.” Target a high share of Experience bullets with measurable results (e.g. toward 70%+) only when the source material honestly supports it—never fabricate to hit a ratio.

You are a senior technical recruiter and resume optimization expert. Your PRIMARY task is to rewrite the Professional Experience section so every bullet aligns with the job description and reads well for both ATS and humans. Updating only the Skills section is NOT acceptable—you must refactor Experience bullets first and thoroughly.

=== STEP 1: EXTRACT FROM JOB DESCRIPTION ===
- From the JD, extract exactly: (a) primary/required skills and technologies, (b) key responsibilities and verbs, (c) tools, frameworks, and methodologies. Use this list to drive all Experience rewrites—do not rely on the base resume wording alone.

=== MANDATORY: PROFESSIONAL EXPERIENCE (workExperience) ===
- You MUST replace (not keep) the bullet text for every job, especially recent/current roles. Recent roles must be rewritten so bullets explicitly reflect the JD's primary and required skills using only tools/outcomes the original resume supports.
- For each Experience bullet: use JD phrasing where it honestly describes the candidate's work. Map background to what the JD asks for; if an original bullet cannot be tied to the JD, replace it with one that can—without adding false tools or employers.
- Each job must have 5–6 bullets where the source material allows; each bullet at least 20 words when possible. Add bullets only to cover JD themes already grounded in that role's original content. Prioritize recent/current roles.
- Preserve ONLY: company names, job titles, and dates (years strings exactly). All bullet text should be revised for JD alignment; default is replace, not keep.
- Use distinct action verbs; use exact tech names from the JD only when they appear in or are clearly equivalent to the candidate's stack in the original resume.

=== OTHER SECTIONS ===
- Summary: Short, keyword-aware, natural readability; mirror top JD themes the candidate can claim.
- Skills (additional.technicalSkills etc.): ATS-oriented list—one skill per line (vertical list, no commas); JD-relevant, qualified terms first; exact spellings from the JD where they match real skills; no stuffing.
- Education: Keep as-is unless the JD emphasizes specific degrees/certifications already on the resume.
- No vague buzzwords (e.g. results-driven, team player, adept at).

=== RECRUITER & ATS ===
- Incorporate JD keywords naturally (tools, methods, responsibilities); prefer exact matches where truthful for ATS.
- Bullets: concise (about one to two lines each); outcome and impact first, not duty dumps.
- Remove or minimize weak filler; keep JSON schema valid and dates unchanged.

=== ANTI-REPETITION (fixes “Repetition” checks) ===
- Same action verb (or obvious synonym) must not start more than two bullets in the entire resume; scan all workExperience + personalProjects descriptions before finalizing.
- Do not reuse identical or near-identical sentence scaffolds across bullets; each line should read distinct (except shared proper nouns / stack names).
- technicalSkills: reorder for JD relevance only; keep every distinct skill from the source—do not drop items to “dedupe”; avoid repeating the same skill string on multiple consecutive lines when editing.

=== STYLE ===
- Each Experience bullet must read differently from the base resume and reflect JD language where truthful.
- Banned vague phrases: "results-driven", "proven track record", "team player", "adept at", "meticulous", "dynamic". Be specific.
- Quantify impact (recruiter standard): prioritize bullets that combine a strong verb with a measurable signal. Rewrite thin bullets so they include numbers, percentages, ranges, team or user scale, frequency, or duration when those facts exist in the source resume or are clearly grounded in the original text. Aim for the majority of Experience bullets to carry at least one concrete quant (same honesty rules as above—no invented metrics).
- Action verb rule: No single opening verb (e.g. developed, led, built, designed, implemented, managed, delivered, optimized) more than twice in the entire resume. Do not use the same or a near-synonym verb to start two adjacent bullets.
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it

Job Description:
{job_description}

Keywords to emphasize (align STEP 1 with this list):
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""


IMPROVE_PROMPT_OPTIONS = [
    {
        "id": "nudge",
        "label": "Light nudge",
        "description": "Minimal edits to better align existing experience.",
    },
    {
        "id": "keywords",
        "label": "Keyword enhance",
        "description": "Blend in relevant keywords without changing role or scope.",
    },
    {
        "id": "full",
        "label": "Full tailor",
        "description": "Comprehensive tailoring using the job description.",
    },
    {
        "id": "other",
        "label": "Deep JD align",
        "description": "Heavy experience rewrites toward the JD; unique verbs; strict honesty limits.",
    },
]

IMPROVE_RESUME_PROMPTS = {
    "nudge": IMPROVE_RESUME_PROMPT_NUDGE,
    "keywords": IMPROVE_RESUME_PROMPT_KEYWORDS,
    "full": IMPROVE_RESUME_PROMPT_FULL,
    "other": IMPROVE_RESUME_PROMPT_OTHER,
}

DEFAULT_IMPROVE_PROMPT_ID = "keywords"

# Backward-compatible alias
IMPROVE_RESUME_PROMPT = IMPROVE_RESUME_PROMPT_FULL

COVER_LETTER_PROMPT = """Write a brief cover letter for this job application.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Candidate Resume (JSON):
{resume_data}

Requirements:
- 100-150 words maximum
- 3-4 short paragraphs
- Opening: Reference ONE specific thing from the job description (product, tech stack, or problem they're solving) - not generic excitement about "the role"
- Middle: Pick 1-2 qualifications from resume that DIRECTLY match stated requirements - prioritize relevance over impressiveness
- Closing: Simple availability to discuss, no desperate enthusiasm
- If resume shows career transition, frame the pivot as intentional and relevant
- Extract company name from job description - do not use placeholders
- Do NOT invent information not in the resume
- Tone: Confident peer, not eager applicant
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it

Output plain text only. No JSON, no markdown formatting."""

OUTREACH_MESSAGE_PROMPT = """Generate a cold outreach message for LinkedIn or email about this job opportunity.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Candidate Resume (JSON):
{resume_data}

Guidelines:
- 70-100 words maximum (shorter than a cover letter)
- First sentence: Reference specific detail from job description (team, product, technical challenge) - never open with "I'm reaching out" or "I saw your posting"
- One sentence on strongest matching qualification with a concrete metric if available
- End with low-friction ask: "Worth a quick chat?" not "I'd love the opportunity to discuss"
- Tone: How you'd message a former colleague, not a stranger
- Do NOT include placeholder brackets
- Do NOT use phrases like "excited about" or "passionate about"
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it

Output plain text only. No JSON, no markdown formatting."""

GENERATE_TITLE_PROMPT = """Extract the job title and company name from this job description.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Rules:
- Format: "Role @ Company" (e.g., "Senior Frontend Engineer @ Stripe")
- If the company name is not found, return just the role (e.g., "Senior Frontend Engineer")
- Maximum 60 characters
- Use the most specific role title mentioned
- Do not add any other text, quotes, or formatting

Output the title only, nothing else."""

# Alias for backward compatibility
RESUME_SCHEMA = RESUME_SCHEMA_EXAMPLE
