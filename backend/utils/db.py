"""
Database helper functions for completion CRUD operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Tuple
import logging

from backend.models import Completion
from backend.schemas import CompletionLog

logger = logging.getLogger(__name__)


def insert_completion(db: Session, log: CompletionLog) -> Completion:
    """Insert a single completion and return the persisted ORM object."""
    obj = Completion(
        prompt=log.prompt,
        response=log.response,
        model=log.model,
        tokens_in=log.tokens_in,
        tokens_out=log.tokens_out,
        latency_ms=log.latency_ms,
        cost_usd=log.cost_usd,
        user_id=log.user_id,
        conversation_id=log.conversation_id,
    )
    db.add(obj)
    db.flush()   # populates obj.id via lastrowid before commit
    db.commit()
    return obj


def batch_insert_completions(
    db: Session, logs: List[CompletionLog]
) -> Tuple[List[Completion], List[Tuple[int, str]]]:
    """
    Insert completions in a single transaction.

    Returns (inserted_objects, errors) where errors is a list of
    (index, reason) tuples for items that failed validation.
    If more than 50 items fail the entire batch is rolled back and
    all items are reported as errors.
    """
    errors: List[Tuple[int, str]] = []
    objects: List[Completion] = []

    for i, log in enumerate(logs):
        try:
            obj = Completion(
                prompt=log.prompt,
                response=log.response,
                model=log.model,
                tokens_in=log.tokens_in,
                tokens_out=log.tokens_out,
                latency_ms=log.latency_ms,
                cost_usd=log.cost_usd,
                user_id=log.user_id,
                conversation_id=log.conversation_id,
            )
            objects.append(obj)
        except Exception as exc:
            errors.append((i, str(exc)))

    if len(errors) > 50:
        return [], [(i, r) for i, r in errors]

    try:
        db.add_all(objects)
        db.flush()   # populates PKs before commit
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Batch insert failed: %s", exc)
        all_errors = [(i, "database error") for i in range(len(logs))]
        return [], all_errors

    return objects, errors


def get_completion_by_id(db: Session, completion_id: int) -> Optional[Completion]:
    """Return a completion by primary key, or None."""
    return db.query(Completion).filter(Completion.id == completion_id).first()
