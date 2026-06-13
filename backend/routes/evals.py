"""
Evaluation endpoints: single completion eval and async batch eval.
"""
from __future__ import annotations

import threading
import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import EvalResult as EvalResultModel, Completion
from backend.evals.text_metrics import TextMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/evals", tags=["evals"])

# In-memory job tracker (good enough without Celery for now)
_JOBS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request / response schemas (local, not worth a separate file)
# ---------------------------------------------------------------------------

class EvalRequest(BaseModel):
    completion_id: int
    eval_types: List[str] = ["llm_judge", "bleu", "rouge"]
    criteria: Optional[str] = "Is this response helpful and accurate?"


class EvalResponse(BaseModel):
    completion_id: int
    scores: dict
    explanation: str
    timestamp: datetime


class BatchEvalRequest(BaseModel):
    completion_ids: List[int]
    eval_types: List[str] = ["llm_judge"]
    sample_rate: float = 1.0


class BatchEvalResponse(BaseModel):
    submitted_count: int
    job_id: str
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_evals(
    db: Session,
    completion: Completion,
    eval_types: List[str],
    criteria: str,
) -> dict:
    """Run requested eval types and return scores dict."""
    scores: dict = {}
    explanation = ""

    if "bleu" in eval_types:
        try:
            scores["bleu"] = TextMetrics.bleu_score(completion.prompt, completion.response)
        except Exception as exc:
            logger.warning("BLEU failed: %s", exc)
            scores["bleu"] = 0.0

    if "rouge" in eval_types:
        try:
            rouge = TextMetrics.rouge_score(completion.prompt, completion.response)
            scores["rouge"] = (rouge["rouge1"] + rouge["rougeL"]) / 2
        except Exception as exc:
            logger.warning("ROUGE failed: %s", exc)
            scores["rouge"] = 0.0

    if "llm_judge" in eval_types:
        try:
            from backend.evals.llm_judge import LLMJudge
            judge = LLMJudge()
            scores["llm_judge"] = judge.evaluate_response(
                completion.prompt, completion.response, criteria
            )
            explanation = judge.get_evaluation_explanation(
                completion.prompt, completion.response, criteria
            )
        except Exception as exc:
            logger.warning("LLM judge failed: %s", exc)
            scores["llm_judge"] = 0.0

    return scores, explanation


def _persist_results(db: Session, completion_id: int, scores: dict) -> None:
    for eval_type, score in scores.items():
        db.add(
            EvalResultModel(
                completion_id=completion_id,
                eval_type=eval_type,
                score=score,
            )
        )
    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvalResponse, status_code=status.HTTP_200_OK)
def evaluate_completion(req: EvalRequest, db: Session = Depends(get_db)):
    """Run evaluations on a single completion and store results."""
    completion = db.query(Completion).filter(Completion.id == req.completion_id).first()
    if not completion:
        raise HTTPException(status_code=404, detail=f"Completion {req.completion_id} not found.")

    scores, explanation = _run_evals(db, completion, req.eval_types, req.criteria or "")
    _persist_results(db, req.completion_id, scores)

    return EvalResponse(
        completion_id=req.completion_id,
        scores=scores,
        explanation=explanation,
        timestamp=datetime.utcnow(),
    )


@router.post("/batch", response_model=BatchEvalResponse, status_code=status.HTTP_202_ACCEPTED)
def batch_evaluate(req: BatchEvalRequest, db: Session = Depends(get_db)):
    """Submit a batch of completions for async evaluation."""
    import random

    ids = req.completion_ids
    if req.sample_rate < 1.0:
        ids = random.sample(ids, max(1, int(len(ids) * req.sample_rate)))

    job_id = f"batch_{uuid.uuid4().hex[:8]}"
    _JOBS[job_id] = {"status": "processing", "total": len(ids), "done": 0}

    # Run in a background thread (no Celery dependency)
    def _worker():
        from backend.database import SessionLocal
        worker_db = SessionLocal()
        try:
            for cid in ids:
                comp = worker_db.query(Completion).filter(Completion.id == cid).first()
                if not comp:
                    continue
                try:
                    scores, _ = _run_evals(worker_db, comp, req.eval_types, "")
                    _persist_results(worker_db, cid, scores)
                except Exception as exc:
                    logger.warning("Batch eval error for %d: %s", cid, exc)
                finally:
                    _JOBS[job_id]["done"] += 1
        finally:
            worker_db.close()
            _JOBS[job_id]["status"] = "complete"

    threading.Thread(target=_worker, daemon=True).start()

    return BatchEvalResponse(
        submitted_count=len(ids),
        job_id=job_id,
        status="processing",
    )


@router.get("/batch/{job_id}")
def get_batch_status(job_id: str):
    """Poll status of a batch evaluation job."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
