"""Job description management endpoints."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.database import db
from app.schemas import (
    JobRegisterRequest,
    JobUploadRequest,
    JobUploadResponse,
    RegisteredApplicationSummary,
    RegisteredApplicationsListResponse,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/upload", response_model=JobUploadResponse)
async def upload_job_descriptions(request: JobUploadRequest) -> JobUploadResponse:
    """Upload one or more job descriptions.

    Stores the raw text for later use in resume tailoring.
    Returns an array of job_ids corresponding to the input array.
    """
    if not request.job_descriptions:
        raise HTTPException(status_code=400, detail="No job descriptions provided")

    job_ids: list[str] = []
    urls = request.source_urls
    companies = request.company_names
    titles = request.job_titles
    for idx, jd in enumerate(request.job_descriptions):
        if not jd.strip():
            raise HTTPException(status_code=400, detail="Empty job description")

        source_url: str | None = None
        if urls is not None and idx < len(urls):
            raw = urls[idx]
            if isinstance(raw, str) and raw.strip():
                source_url = raw.strip()

        company_name: str | None = None
        if companies is not None and idx < len(companies):
            raw_co = companies[idx]
            if isinstance(raw_co, str) and raw_co.strip():
                company_name = raw_co.strip()

        job_title: str | None = None
        if titles is not None and idx < len(titles):
            raw_title = titles[idx]
            if isinstance(raw_title, str) and raw_title.strip():
                job_title = raw_title.strip()

        job = db.create_job(
            content=jd.strip(),
            resume_id=request.resume_id,
            source_url=source_url,
            company_name=company_name,
            job_title=job_title,
        )
        job_ids.append(job["job_id"])

    return JobUploadResponse(
        message="data successfully processed",
        job_id=job_ids,
        request={
            "job_descriptions": request.job_descriptions,
            "source_urls": request.source_urls,
            "company_names": request.company_names,
            "job_titles": request.job_titles,
            "resume_id": request.resume_id,
        },
    )


@router.post("/register", response_model=JobUploadResponse)
async def register_job_application(request: JobRegisterRequest) -> JobUploadResponse:
    """Register job application fields without generating a tailored resume."""
    company = request.company_name.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company name is required")

    content = request.content.strip()
    if not content:
        content = "(Application registered — add job description before tailoring)"

    source_url: str | None = None
    if request.source_url and request.source_url.strip():
        source_url = request.source_url.strip()

    job_title = request.job_title.strip() or None

    job = db.create_job(
        content=content,
        resume_id=request.resume_id,
        source_url=source_url,
        company_name=company,
        job_title=job_title,
    )

    return JobUploadResponse(
        message="Application registered",
        job_id=[job["job_id"]],
        request={
            "resume_id": request.resume_id,
            "company_name": company,
            "job_title": job_title,
            "content": content,
            "source_url": source_url,
        },
    )


@router.get("/applications", response_model=RegisteredApplicationsListResponse)
async def list_registered_applications(
    parent_id: str | None = Query(
        None, description="Optional master resume ID to filter applications"
    ),
) -> RegisteredApplicationsListResponse:
    """List job applications saved without a tailored resume (register-only or abandoned)."""
    if parent_id:
        master = db.get_resume(parent_id)
        if not master:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not master.get("is_master"):
            raise HTTPException(
                status_code=400,
                detail="parent_id must be a master resume ID",
            )

    jobs = db.list_registered_applications(parent_id)
    summaries: list[RegisteredApplicationSummary] = []
    for job in jobs:
        rid = job.get("resume_id") or ""
        su = job.get("source_url")
        source_url = su.strip() if isinstance(su, str) and su.strip() else None
        cn = job.get("company_name")
        company_name = cn.strip() if isinstance(cn, str) and cn.strip() else None
        jt = job.get("job_title")
        job_title = jt.strip() if isinstance(jt, str) and jt.strip() else None
        summaries.append(
            RegisteredApplicationSummary(
                job_id=job.get("job_id", ""),
                master_resume_id=rid,
                company_name=company_name,
                job_title=job_title,
                source_url=source_url,
                created_at=job.get("created_at", ""),
            )
        )

    return RegisteredApplicationsListResponse(request_id=str(uuid4()), data=summaries)


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    """Get job description by ID."""
    job = db.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
