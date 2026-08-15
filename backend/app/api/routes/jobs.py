from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session

from backend.app.api.deps import get_job_or_404
from backend.app.db.models import AnalysisJob, utc_now
from backend.app.db.session import get_session
from backend.app.schemas.job import AnalysisJobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=AnalysisJobRead)
def get_job(
    job: AnalysisJob = Depends(get_job_or_404),
) -> AnalysisJobRead:
    return AnalysisJobRead.model_validate(job)


@router.post("/{job_id}/cancel", response_model=AnalysisJobRead)
def cancel_job(
    job: AnalysisJob = Depends(get_job_or_404),
    session: Session = Depends(get_session),
) -> AnalysisJobRead:
    if job.status == "queued":
        job.status = "canceled"
        job.current_step = "Canceled"
    elif job.status == "running":
        job.status = "cancel_requested"
        job.current_step = "Cancel requested"
    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)
    return AnalysisJobRead.model_validate(job)


@router.post("/{job_id}/retry", response_model=AnalysisJobRead)
def retry_job(
    background_tasks: BackgroundTasks,
    job: AnalysisJob = Depends(get_job_or_404),
    session: Session = Depends(get_session),
) -> AnalysisJobRead:
    from backend.app.api.routes import analysis as analysis_routes

    # A failed job usually got part way, so resume the remainder rather than
    # paying for every photo again.
    retry = analysis_routes.queue_analysis_job(
        session, background_tasks, job.trip_id, "missing"
    )
    return AnalysisJobRead.model_validate(retry)
