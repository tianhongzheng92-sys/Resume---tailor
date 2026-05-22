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

**Alignment target (honest):** Tune wording so keyword match, skills alignment, experience relevance, and seniority fit would *typically* land in the 70–90% range when the candidate's real background honestly supports that level of fit. If the resume and JD only partially overlap, preserve truthfulness over score; do not add skills, employers, tools, or metrics to fake alignment.

**One resume, two goals:** Produce a single JSON resume that simultaneously:
- **ATS track:** Weave important JD keywords naturally; use recognizable tool/stack spellings from the JD when they match real experience; keep lists scannable; avoid stuffing and redundant keyword repetition.
- **Recruiter track:** Keep bullets clean and concise (about 1–2 lines each); use strong, varied action verbs; lead with outcomes and impact, not generic responsibilities.

**Tailoring:** Map experience to JD responsibilities and requirements only where the source resume supports it. Prioritize impact over task lists; remove or reduce irrelevant or low-impact content where your mode rules allow. Keep values ATS-friendly plain text (no markdown tables inside strings).

**Metrics:** First, count how many bullets per role already contain numbers or clear scale in the original—your output must keep that level of quantification (same or higher share of quantified bullets per job), not zero it out. Aim for a high share (e.g. 70%+) of bullets with a measurable line only where the source supports it—never invent or "estimate" metrics to hit a ratio. Never remove existing %, $, counts, or timelines to sound simpler; rephrase around them if needed. In minimal-edit modes, preserve every figure from the source.

=== SOFT SKILLS ALIGNMENT BOOST (NO FABRICATION) ===

Goal:
Improve soft skills match rate to align with job description expectations while preserving factual accuracy and avoiding exaggeration.

Instructions:
- Extract soft skills explicitly or implicitly required in the job description (e.g., collaboration, communication, ownership, leadership, stakeholder management, adaptability, problem-solving).
- Identify where these soft skills already exist implicitly in the candidate’s experience.
- Rewrite bullet points to naturally embed these soft skills into existing responsibilities and achievements.
- Do NOT add new experiences, roles, or claims. Only enhance wording of existing content.
- Do NOT add soft skills as standalone statements. Always integrate them into achievements or actions.

Embedding patterns (use naturally, not repetitively):
- Collaborated with cross-functional teams to...
- Communicated with stakeholders to...
- Led or mentored team members to...
- Coordinated with product or design teams to...
- Drove decision-making by...
- Improved team efficiency by...
- Partnered with engineers or clients to...

Constraints:
- Maintain concise bullet length (1–2 lines)
- Preserve all existing metrics and quantified data
- Do not increase verbosity unnecessarily
- Avoid keyword stuffing or repeating the same soft skill phrasing
- Ensure variation in sentence structure and verbs

Priority soft skills to emphasize when supported by source:
- Collaboration
- Communication
- Ownership or accountability
- Leadership or mentorship
- Problem-solving
- Adaptability
- Stakeholder management

Output impact:
- Increase perceived soft skill alignment for recruiter evaluation
- Improve ATS keyword matching without compromising readability"""

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
- Preserve all numbers, percentages, currency amounts, and quantitative outcomes in work experience and project bullets exactly as written (do not strip metrics when normalizing wording).
- Technical skills (section titles like Skills, Technical Skills, Technologies, Tools, Core Competencies): MUST go in `additional.technicalSkills` as a JSON array of strings with ONE skill per element (e.g. ["Python", "AWS", "Kubernetes"]). If the resume lists skills separated by commas or pipes on one line, split them into separate array elements. Do NOT put the only copy of skills only in `customSections` unless the section is non-technical; prefer `additional.technicalSkills` for standard skill lists.

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

Rules for required_skills, preferred_skills, and keywords (used for resume matching):
- Use SHORT, atomic tokens a candidate would type on a resume: tool names, languages, frameworks, platforms (e.g. "Python", "AWS", "Kubernetes", "PostgreSQL"), not full sentences.
- Prefer the spelling the JD uses for each technology; include one canonical entry per concept (avoid listing the same idea three ways across lists).
- Put must-haves in required_skills, nice-to-haves in preferred_skills, and domain/process terms (e.g. "microservices", "CI/CD", "Agile") in keywords.
- Do NOT put long JD phrases, entire bullet sentences, or duplicate the same term in multiple lists—each distinct token should appear once, in the strongest appropriate list only.
- Omit vague filler that never appears as a literal resume keyword (e.g. "strong communication skills") unless the JD names a specific method or credential.
- Extract numeric years (e.g., "5+ years" → 5) and infer seniority level.

Job description:
{job_description}"""

CRITICAL_TRUTHFULNESS_RULES_TEMPLATE = """CRITICAL TRUTHFULNESS RULES - NEVER VIOLATE:
1. DO NOT invent numeric achievements (e.g., "increased by 30%") unless they exist in original
2. DO NOT add company names, product names, or technical terms not in the original
3. DO NOT add languages, frameworks, or platforms the candidate hasn't used
4. DO NOT extend employment dates or change timelines. Copy date ranges exactly as they appear, including months.
5. Preserve factual accuracy - only use information provided by the candidate
6. Avoid repeating action verbs and phrases on your resume
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
- Quantify impact (light touch): where a bullet already states or clearly implies scale, time, counts, or percentages, keep or surface that signal in plain form; do not add new numbers. **Never drop existing figures** when rephrasing (same values, clearer sentence).
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
- Align bullets with JD-required skills, tools, and responsibilities only where the resume supports them; emphasize recent and most relevant roles first in how you rephrase (keep section order unless reordering bullets within a role improves relevance).
- Strong, varied action verbs; avoid repeating the same opening verb across adjacent bullets.
- Anti-repetition (common “Repetition” score failure): across ALL workExperience and personalProjects bullets combined, each major opening verb (e.g. developed, built, led, designed, implemented, managed, delivered, optimized, automated, streamlined, executed, used) may appear at most twice as the first word of a bullet—use synonyms and different sentence shapes. Do not reuse the same multi-word template or clause opener across bullets unless it is a proper noun or tool name.
- Impact over duties: lead bullets with outcomes the source supports; keep each bullet concise (about one or two lines of text).
- Tighten or shorten low-relevance wording; do not delete required structure (same bullet counts per truthfulness rules).
- You may rephrase bullet points to include keyword phrasing
- For customSections: preserve exact structure, item count, titles, subtitles, and years. If an item's description is an empty array [] in the original, keep it empty []. Do NOT generate descriptions for items that had none.
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it
- Skills: One skill per line (vertical list, no commas). Include all JD-relevant skills the candidate is qualified for.
- Quantify impact: rewrite weaker bullets so they lead with or include concrete metrics where the resume already supports them (percentages, counts, team size, latency, savings, users, release cadence, data volume, duration). Make implicit scale explicit when it is clearly grounded in the original text. Never invent statistics; do not infer or estimate numbers to “fill in” gaps—where the source had no metric, keep qualitative wording; **where the source had a metric, you must keep it** (do not drop numbers to avoid guessing).
- Aim for a high share of bullets with measurable signals when the source allows; never fabricate to hit a percentage target. **Preserve the original resume’s density of quantified bullets per role**—do not systematically remove figures.

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
- Use strong, varied action verbs; avoid repeating the same opening verb on adjacent bullets. Do not invent quantifiable achievements not in the original; **retain every quantifiable figure that is in the original** when you rephrase.
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
- Quantify impact: increase recruiter-ready evidence by weaving specific numbers into bullets wherever the original resume already provides or strongly implies them (e.g. performance gains, error rates, throughput, headcount, budget, timelines, adoption). Reframe vague lines into outcome + metric when the source supports it. Do not fabricate figures; do not infer “reasonable estimates.” Where the original had no number, stay qualitative; **where it had a number, keep it**—never delete real metrics to shorten bullets.
- Aim for most Experience bullets to include a measurable element when the resume can support it; never invent to reach a quota. **Match or exceed the source’s rate of quantified bullets per role** (bullets containing at least one numeric or scale signal).
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

IMPORTANT: Generate ALL text content (summary, descriptions, skills) in {output_language}.
Do NOT include personalInfo in your output - it will be preserved from the original resume.

=== OUTPUT & SCOPE (JSON—read first) ===
- Your output is valid JSON only (schema at the end). Field `workExperience[].description` is an array of bullet strings: that is the Professional Experience body. `summary` is a single string. `additional.technicalSkills` is the Skills list.
- **You must change Professional Experience bullets, not only the summary.** A result that rewrites summary (and maybe skills) but leaves `workExperience[].description` mostly unchanged is a failure. Refactor every role's bullets per the rules below.
- Plain text inside those JSON strings only: no markdown, no "---" dividers, no section headers like "Summary:" or "Professional Experience:" inside a bullet.
- Use the full Job Description plus the Keywords list for STEP 1; do not ignore them.
- Apply the same JD-alignment discipline to `personalProjects` when project facts support it. For `customSections`: preserve exact structure, item count, ids, titles, subtitles, and years; improve description text only where the original had content and facts support JD phrasing.
- Copy every workExperience (and project) `years` value EXACTLY from the original (including months). Do not shorten or reformat.
- **Metrics (truthfulness):** Preserve every number, percentage, and metric from the source for that role. You may rephrase around them; never invent or estimate to sound stronger. Aim for **at least ~75%** of workExperience bullets across the resume to include a measurable signal (number, %, range, team/user scale, duration, frequency, throughput) **when the source material for that role honestly supports that density**—never fabricate to hit the ratio; use concrete non-numeric scope where no figure exists. Do not replace metric-heavy bullets with vague duty lines.

You are a world-class technical resume assistant. Your PRIMARY task is to rewrite the Professional Experience section so every bullet aligns with the job description. Updating only the Skills section (or only the summary) is NOT acceptable—you must refactor Experience bullets first and thoroughly.

=== STEP 1: EXTRACT FROM JOB DESCRIPTION ===
- From the JD, extract exactly: (a) primary/required skills and technologies, (b) key responsibilities and verbs, (c) tools, frameworks, and methodologies. Use this list to drive all Experience rewrites—do not rely on the base resume wording alone.

=== MANDATORY: PROFESSIONAL EXPERIENCE (`workExperience`) ===
- You MUST replace (not keep) the bullet text for every job, especially recent/current roles. Recent roles must be rewritten so bullets explicitly reflect the JD's primary and required skills **using only tools, outcomes, and employers the original resume supports** (truthfulness rules override literal JD tools the candidate never used).
- For each Experience bullet: use JD-aligned phrasing and outcome language where it honestly describes the candidate's work. Map background to what the JD asks for; if an original bullet is generic or misses a JD theme you can support from that role's facts, replace it with one that does—without adding false tools, companies, or metrics.
- When the JD names a skill or tool, prefer that exact term **only if** it appears in or is clearly equivalent to the candidate's stack in the original resume; otherwise use honest wording from the source.
- Each job must have **5–6 bullets** where the source material allows; each bullet **at least ~20 words** when possible. Add bullets only to cover JD themes grounded in that role's original content. Prioritize recent/current roles for the strongest alignment.
- Preserve ONLY: company names, job titles, and dates (`years` strings exactly). All bullet text must be revised for JD alignment; default is **replace**, not keep.
- Use **unique opening action verbs** per bullet; lead with outcomes. Include preserved or clearly implied numbers/percentages from the source; do not add new ones.

=== OTHER SECTIONS ===
- **Summary:** Integrate the top skills and requirements from the JD that the candidate can truthfully claim; keep it keyword-aware but natural and readable.
- **Skills** (`additional.technicalSkills`, etc.): One skill per line (vertical list in the array, no comma-separated mega-strings). Include all JD-relevant skills the candidate is qualified for; exact JD spellings where they match real skills; no stuffing.
- **Education:** Keep as-is unless the JD emphasizes specific degrees/certifications already on the resume.
- No vague buzzwords (e.g. results-driven, team player, adept at). No "---" or fake section separators inside JSON values.

=== RECRUITER & ATS ===
- Weave JD keywords naturally (tools, methods, responsibilities); prefer exact matches where truthful for ATS.
- Bullets: about one to two lines each where possible; outcome and impact first, not duty dumps.
- Remove weak filler only; **numeric outcomes are never filler—do not strip them.**

=== ANTI-REPETITION (mandatory) ===
- **Global verb cap:** No opening action verb (e.g. developed, led, built, designed, implemented, managed, delivered, optimized, automated, streamlined) may appear more than **twice** as the first word of any bullet across **all** workExperience + personalProjects descriptions combined. Scan the full resume before finalizing.
- **Adjacency:** Never start two consecutive bullets (within the same job or across jobs) with the same verb or an obvious synonym.
- Do not reuse identical or near-identical sentence scaffolds across bullets; each line should read distinct (except shared proper nouns / stack names).
- **technicalSkills:** Reorder for JD relevance only; keep every distinct skill from the source; do not drop items to dedupe; avoid repeating the same skill on consecutive lines.

=== STYLE ===
- Each Experience bullet must read **differently** from the base resume and reflect JD language and keywords where truthful.
- Banned vague or buzzwordy phrasing—be concise and specific: e.g. avoid "results-driven", "proven track record", "team player", "adept at", "meticulous", "dynamic". Use concrete achievements and skills from the source.
- **Quantify:** Preserve all original numbers, percentages, and metrics. Surface clearly implied scale from the source where no digit exists. Target **≥75%** of Experience bullets with a measurable line only when honest given the source; never invent to reach the target.
- **Action verbs:** Start each bullet with a strong, distinct action verb; respect the global twice-max and no-adjacent-synonym rules above.
- Do NOT use em dash ("—") anywhere in the output, even if present in the source (use commas or periods).

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
        "description": "Rewrites all experience bullets to the JD (include summary); quantify + anti-repetition; strict honesty.",
    },
]

IMPROVE_RESUME_PROMPTS = {
    "nudge": IMPROVE_RESUME_PROMPT_NUDGE,
    "keywords": IMPROVE_RESUME_PROMPT_KEYWORDS,
    "full": IMPROVE_RESUME_PROMPT_FULL,
    "other": IMPROVE_RESUME_PROMPT_OTHER,
}

DEFAULT_IMPROVE_PROMPT_ID = "other"

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

GENERATE_TITLE_PROMPT = """Extract the JOB TITLE and COMPANY hiring for that role from the posting.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Rules:
- IGNORE marketing blurbs, "About us", "We believe", "Join our team" story paragraphs, and boilerplate. Find the actual position name (often near the top or after a "Job title" / "Position" label).
- Output EXACTLY ONE LINE in this format: "Role @ Company" (e.g. "Senior Frontend Engineer @ Stripe"). Use ASCII @ with one space on each side.
- If the employer name is unclear, output role only: "Senior Frontend Engineer" (no @, no extra words).
- Role = short job title (a few words), not a full sentence. Company = legal or brand hiring name only (one to four words typical), not a tagline.
- Maximum 60 characters for the whole line. No quotes, no bullets, no newlines, no second sentence.

Output the single title line only, nothing else."""

GENERATE_TITLE_ROLE_ONLY_PROMPT = """Extract the JOB TITLE from the posting.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Rules:
- IGNORE marketing blurbs and "About us" sections. Find the actual position name.
- Output ONLY the role title (a few words), not a sentence. No company name (the employer is registered separately).
- No @ symbol, no quotes, no bullets, no newlines.
- Maximum 50 characters.

Output the role title only, nothing else."""

# Alias for backward compatibility
RESUME_SCHEMA = RESUME_SCHEMA_EXAMPLE
