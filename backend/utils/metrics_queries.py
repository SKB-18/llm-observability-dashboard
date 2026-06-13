"""
SQLAlchemy aggregation queries for metrics endpoints.

All functions accept optional start/end datetimes; None means unbounded.
Percentile_cont is a PostgreSQL extension – for SQLite we fall back to
a Python-side sort so tests run without Postgres.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import statistics

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.models import Completion, EvalResult


def _apply_date_filter(query, start: Optional[datetime], end: Optional[datetime]):
    if start:
        query = query.filter(Completion.timestamp >= start)
    if end:
        query = query.filter(Completion.timestamp <= end)
    return query


def query_summary(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """Return aggregate summary metrics — LMSYS source only (real production data)."""
    q = session.query(
        func.count(Completion.id).label("total_requests"),
        func.sum(Completion.cost_usd).label("total_cost_usd"),
        func.avg(Completion.latency_ms).label("avg_latency_ms"),
        func.count(func.distinct(Completion.user_id)).label("unique_users"),
        func.sum(case((Completion.tokens_out > 0, 1), else_=0)).label("success_count"),
    ).filter(Completion.source == "lmsys")
    q = _apply_date_filter(q, start, end)
    row = q.one()

    models = (
        _apply_date_filter(
            session.query(func.distinct(Completion.model))
            .filter(Completion.source == "lmsys"),
            start, end,
        ).all()
    )

    total = row.total_requests or 0
    success = row.success_count or 0
    success_rate = round((success / total) * 100, 2) if total > 0 else 100.0

    return {
        "period": {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        },
        "total_requests": total,
        "total_cost_usd": round(row.total_cost_usd or 0.0, 6),
        "avg_latency_ms": round(row.avg_latency_ms or 0.0, 2),
        "models": [m[0] for m in models if m[0]],
        "success_rate_percent": success_rate,
        "unique_users": row.unique_users or 0,
    }


def query_by_model(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    """Per-model aggregate stats — LMSYS source only, sorted by request_count DESC."""
    q = session.query(
        Completion.model,
        func.count(Completion.id).label("request_count"),
        func.avg(Completion.latency_ms).label("avg_latency_ms"),
        func.sum(Completion.cost_usd).label("total_cost_usd"),
        func.avg(Completion.tokens_in).label("avg_tokens_in"),
        func.avg(Completion.tokens_out).label("avg_tokens_out"),
        func.sum(case((Completion.tokens_out > 0, 1), else_=0)).label("success_count"),
    ).filter(Completion.source == "lmsys").group_by(Completion.model)
    q = _apply_date_filter(q, start, end)
    rows = q.order_by(func.count(Completion.id).desc()).all()

    results = []
    for row in rows:
        # Fetch raw latencies for this model to compute percentiles in Python
        lats = _fetch_latencies(session, start, end, model=row.model)
        p = _percentiles(lats)
        results.append(
            {
                "model": row.model,
                "request_count": row.request_count,
                "avg_latency_ms": round(row.avg_latency_ms or 0.0, 2),
                "p50_latency_ms": p["p50"],
                "p95_latency_ms": p["p95"],
                "p99_latency_ms": p["p99"],
                "total_cost_usd": round(row.total_cost_usd or 0.0, 6),
                "avg_tokens_in": round(row.avg_tokens_in or 0.0, 1),
                "avg_tokens_out": round(row.avg_tokens_out or 0.0, 1),
                "success_rate_percent": round((row.success_count / row.request_count) * 100, 2) if row.request_count else 100.0,
            }
        )
    return results


def query_by_hour(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    """Hourly bucketed metrics, sorted ASC. Works on both SQLite and PostgreSQL."""
    # Use strftime for SQLite, date_trunc for Postgres
    dialect = session.bind.dialect.name if session.bind else "sqlite"

    if dialect == "postgresql":  # pragma: no cover  — requires a live PG server
        hour_expr = func.date_trunc("hour", Completion.timestamp)
    else:
        # SQLite: truncate to hour via strftime
        hour_expr = func.strftime("%Y-%m-%dT%H:00:00", Completion.timestamp)

    q = session.query(
        hour_expr.label("hour"),
        func.count(Completion.id).label("requests"),
        func.avg(Completion.cost_usd).label("avg_cost_usd"),
        func.avg(Completion.latency_ms).label("avg_latency_ms"),
        func.sum(case((Completion.tokens_out > 0, 1), else_=0)).label("success_count"),
        func.avg(Completion.tokens_in).label("avg_tokens_in"),
        func.avg(Completion.tokens_out).label("avg_tokens_out"),
    ).filter(Completion.source == "lmsys").group_by(hour_expr)
    q = _apply_date_filter(q, start, end)
    rows = q.order_by(hour_expr.asc()).all()

    # Compute per-hour latency percentiles in a single extra query
    lat_q = session.query(
        hour_expr.label("hour"),
        Completion.latency_ms,
    ).filter(Completion.source == "lmsys", Completion.latency_ms.isnot(None))
    lat_q = _apply_date_filter(lat_q, start, end)

    hour_lats: dict = {}
    for lat_row in lat_q.all():
        hour_lats.setdefault(str(lat_row.hour), []).append(lat_row.latency_ms)

    result = []
    for row in rows:
        h = str(row.hour)
        p = _percentiles(hour_lats.get(h, []))
        result.append(
            {
                "hour": h,
                "requests": row.requests,
                "avg_cost_usd": round(row.avg_cost_usd or 0.0, 6),
                "avg_latency_ms": round(row.avg_latency_ms or 0.0, 2),
                "p50": p["p50"],
                "p95": p["p95"],
                "p99": p["p99"],
                "success_count": row.success_count or 0,
                "avg_tokens_in": round(row.avg_tokens_in or 0.0, 1),
                "avg_tokens_out": round(row.avg_tokens_out or 0.0, 1),
            }
        )
    return result


def query_percentiles(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    model: Optional[str] = None,
) -> dict:
    """Latency percentiles. Falls back to Python-side sort (works on SQLite)."""
    lats = _fetch_latencies(session, start, end, model=model)
    p = _percentiles(lats)
    return {
        "model": model,
        **p,
    }


def query_cost_breakdown(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """Total cost, broken down by model and by hour."""
    # total
    q = _apply_date_filter(
        session.query(func.sum(Completion.cost_usd)), start, end
    )
    total = q.scalar() or 0.0

    # by model
    model_rows = _apply_date_filter(
        session.query(
            Completion.model,
            func.sum(Completion.cost_usd).label("cost"),
        ).group_by(Completion.model),
        start,
        end,
    ).all()
    by_model = {r.model: round(r.cost or 0.0, 6) for r in model_rows}

    # by hour
    by_hour = [
        {"hour": row["hour"], "cost": round(row["avg_cost_usd"] * row["requests"], 6)}
        for row in query_by_hour(session, start, end)
    ]

    return {
        "total_cost": round(total, 6),
        "by_model": by_model,
        "by_hour": by_hour,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_latencies(
    session: Session,
    start: Optional[datetime],
    end: Optional[datetime],
    model: Optional[str] = None,
) -> List[float]:
    q = session.query(Completion.latency_ms).filter(Completion.source == "lmsys")
    q = _apply_date_filter(q, start, end)
    if model:
        q = q.filter(Completion.model == model)
    return [row[0] for row in q.all() if row[0] is not None]


def _percentiles(values: List[float]) -> dict:
    if not values:
        return {"p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0, "min": 0, "max": 0}
    s = sorted(values)
    n = len(s)

    def pct(p: float) -> float:
        idx = (p / 100) * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (idx - lo), 2)

    return {
        "p50": pct(50),
        "p75": pct(75),
        "p90": pct(90),
        "p95": pct(95),
        "p99": pct(99),
        "min": round(s[0], 2),
        "max": round(s[-1], 2),
    }


def query_by_source(
    session: Session,
    source: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """Return summary + by-model stats scoped to a single data source."""
    q = session.query(
        func.count(Completion.id).label("total_requests"),
        func.sum(Completion.cost_usd).label("total_cost_usd"),
        func.avg(Completion.latency_ms).label("avg_latency_ms"),
        func.sum(case((Completion.tokens_out > 0, 1), else_=0)).label("success_count"),
        func.count(func.distinct(Completion.model)).label("model_count"),
    ).filter(Completion.source == source)
    q = _apply_date_filter(q, start, end)
    row = q.one()

    model_rows = (
        session.query(
            Completion.model,
            func.count(Completion.id).label("request_count"),
            func.avg(Completion.latency_ms).label("avg_latency_ms"),
            func.sum(Completion.cost_usd).label("total_cost_usd"),
        )
        .filter(Completion.source == source)
        .group_by(Completion.model)
        .order_by(func.count(Completion.id).desc())
    )
    model_rows = _apply_date_filter(model_rows, start, end)

    total = row.total_requests or 0
    success_rate = round((row.success_count / total) * 100, 2) if total > 0 else 100.0

    return {
        "source": source,
        "total_requests": total,
        "total_cost_usd": round(row.total_cost_usd or 0.0, 6),
        "avg_latency_ms": round(row.avg_latency_ms or 0.0, 2),
        "model_count": row.model_count or 0,
        "success_rate_percent": success_rate,
        "by_model": [
            {
                "model": r.model,
                "request_count": r.request_count,
                "avg_latency_ms": round(r.avg_latency_ms or 0.0, 2),
                "total_cost_usd": round(r.total_cost_usd or 0.0, 6),
            }
            for r in model_rows.all()
        ],
    }


def query_model_comparison(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """
    Per-model win rates from LMSYS human_preference evals.

    Returns win / tie / loss counts and win-rate percentage for every model
    that appears in source='lmsys' completions, sorted by win_tie_rate DESC.
    """
    hp_rows = (
        session.query(
            Completion.model,
            func.count(EvalResult.id).label("battles"),
            func.sum(case((EvalResult.score == 1.0, 1), else_=0)).label("wins"),
            func.sum(case((EvalResult.score == 0.5, 1), else_=0)).label("ties"),
            func.sum(case((EvalResult.score == 0.0, 1), else_=0)).label("losses"),
            func.avg(Completion.latency_ms).label("avg_latency_ms"),
            func.avg(Completion.cost_usd).label("avg_cost_usd"),
        )
        .join(EvalResult, EvalResult.completion_id == Completion.id)
        .filter(
            Completion.source == "lmsys",
            EvalResult.eval_type == "human_preference",
        )
        .group_by(Completion.model)
    )
    if start:
        hp_rows = hp_rows.filter(Completion.timestamp >= start)
    if end:
        hp_rows = hp_rows.filter(Completion.timestamp <= end)

    results = []
    for r in hp_rows.all():
        battles = r.battles or 1
        win_rate = round(r.wins / battles, 4)
        win_tie_rate = round((r.wins + r.ties * 0.5) / battles, 4)
        results.append({
            "model": r.model,
            "battles": r.battles,
            "wins": r.wins,
            "ties": r.ties,
            "losses": r.losses,
            "win_rate": win_rate,
            "win_rate_pct": round(win_rate * 100, 1),
            "win_tie_rate": win_tie_rate,
            "win_tie_rate_pct": round(win_tie_rate * 100, 1),
            "avg_latency_ms": round(r.avg_latency_ms or 0.0, 2),
            "avg_cost_usd": round(r.avg_cost_usd or 0.0, 6),
        })

    results.sort(key=lambda x: x["win_tie_rate"], reverse=True)

    return {
        "source": "lmsys",
        "note": "Human preference from LMSYS Chatbot Arena real battles",
        "total_battles": sum(r["battles"] for r in results),
        "models": results,
    }


def query_eval_summary(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """
    Side-by-side summary of both data sources.

    Shows what LMSYS provides (production metrics + win rates) separately
    from what evals_benchmark provides (quality scores).
    """
    # --- LMSYS side ---
    lmsys_comp = (
        session.query(
            func.count(Completion.id).label("n"),
            func.count(func.distinct(Completion.model)).label("models"),
            func.avg(Completion.latency_ms).label("avg_latency_ms"),
            func.sum(Completion.cost_usd).label("total_cost_usd"),
        )
        .filter(Completion.source == "lmsys")
    )
    if start:
        lmsys_comp = lmsys_comp.filter(Completion.timestamp >= start)
    if end:
        lmsys_comp = lmsys_comp.filter(Completion.timestamp <= end)
    lrow = lmsys_comp.one()

    lmsys_hp = (
        session.query(func.count(EvalResult.id))
        .join(Completion, EvalResult.completion_id == Completion.id)
        .filter(Completion.source == "lmsys", EvalResult.eval_type == "human_preference")
        .scalar() or 0
    )

    # --- Benchmark side ---
    bench_comp = (
        session.query(func.count(Completion.id))
        .filter(Completion.source == "evals_benchmark")
        .scalar() or 0
    )

    bench_evals = (
        session.query(
            EvalResult.eval_type,
            func.count(EvalResult.id).label("n"),
            func.avg(EvalResult.score).label("avg"),
            func.min(EvalResult.score).label("min"),
            func.max(EvalResult.score).label("max"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .filter(Completion.source == "evals_benchmark")
        .group_by(EvalResult.eval_type)
        .all()
    )

    quality_scores = {
        r.eval_type: {
            "count": r.n,
            "avg": round(r.avg or 0.0, 4),
            "min": round(r.min or 0.0, 4),
            "max": round(r.max or 0.0, 4),
        }
        for r in bench_evals
    }

    return {
        "lmsys": {
            "description": "Real production metrics from LMSYS Chatbot Arena",
            "completions": lrow.n or 0,
            "models": lrow.models or 0,
            "avg_latency_ms": round(lrow.avg_latency_ms or 0.0, 2),
            "total_cost_usd": round(lrow.total_cost_usd or 0.0, 4),
            "human_preference_evals": lmsys_hp,
            "use_for": ["cost analysis", "latency monitoring", "model win rates"],
        },
        "evals_benchmark": {
            "description": "Response quality benchmarks on real prompt/response pairs",
            "completions": bench_comp,
            "quality_scores": quality_scores,
            "use_for": ["BLEU/ROUGE scoring", "LLM judge quality", "benchmark comparison"],
        },
    }


def query_eval_analytics(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """Eval score analytics: per-type averages, score distribution buckets, trend by hour."""

    # Base query joined to completions for date filtering
    def _base():
        q = session.query(EvalResult).join(
            Completion, EvalResult.completion_id == Completion.id
        )
        if start:
            q = q.filter(Completion.timestamp >= start)
        if end:
            q = q.filter(Completion.timestamp <= end)
        return q

    # 1. Per eval-type: avg, min, max, count
    rows = (
        session.query(
            EvalResult.eval_type,
            func.count(EvalResult.id).label("count"),
            func.avg(EvalResult.score).label("avg_score"),
            func.min(EvalResult.score).label("min_score"),
            func.max(EvalResult.score).label("max_score"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .group_by(EvalResult.eval_type)
    )
    if start:
        rows = rows.filter(Completion.timestamp >= start)
    if end:
        rows = rows.filter(Completion.timestamp <= end)

    by_type = [
        {
            "eval_type": r.eval_type,
            "count": r.count,
            "avg_score": round(r.avg_score or 0.0, 4),
            "min_score": round(r.min_score or 0.0, 4),
            "max_score": round(r.max_score or 0.0, 4),
        }
        for r in rows.all()
    ]

    # 2. Score distribution buckets (0-0.2, 0.2-0.4, … 0.8-1.0) — all eval types
    all_scores = [r.score for r in _base().all() if r.score is not None]
    buckets = [
        {"range": "0–20%",  "count": sum(1 for s in all_scores if s <  0.2)},
        {"range": "20–40%", "count": sum(1 for s in all_scores if 0.2 <= s < 0.4)},
        {"range": "40–60%", "count": sum(1 for s in all_scores if 0.4 <= s < 0.6)},
        {"range": "60–80%", "count": sum(1 for s in all_scores if 0.6 <= s < 0.8)},
        {"range": "80–100%","count": sum(1 for s in all_scores if s >= 0.8)},
    ]

    # 3. Hourly avg score trend (all types combined)
    dialect = session.bind.dialect.name if session.bind else "sqlite"
    if dialect == "postgresql":  # pragma: no cover
        hour_expr = func.date_trunc("hour", Completion.timestamp)
    else:
        hour_expr = func.strftime("%Y-%m-%dT%H:00:00", Completion.timestamp)

    trend_rows = (
        session.query(
            hour_expr.label("hour"),
            func.avg(EvalResult.score).label("avg_score"),
            func.count(EvalResult.id).label("count"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .group_by(hour_expr)
        .order_by(hour_expr.asc())
    )
    if start:
        trend_rows = trend_rows.filter(Completion.timestamp >= start)
    if end:
        trend_rows = trend_rows.filter(Completion.timestamp <= end)

    trend = [
        {
            "hour": str(r.hour),
            "avg_score": round(r.avg_score or 0.0, 4),
            "count": r.count,
        }
        for r in trend_rows.all()
    ]

    # 4. Per-model avg score (for QualityChart — real data, not token formula)
    model_rows = (
        session.query(
            Completion.model,
            EvalResult.eval_type,
            func.avg(EvalResult.score).label("avg_score"),
            func.count(EvalResult.id).label("count"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .group_by(Completion.model, EvalResult.eval_type)
    )
    if start:
        model_rows = model_rows.filter(Completion.timestamp >= start)
    if end:
        model_rows = model_rows.filter(Completion.timestamp <= end)

    # Pivot: {model: {eval_type: avg_score}}
    by_model: dict = {}
    for r in model_rows.all():
        by_model.setdefault(r.model, {})[r.eval_type] = round(r.avg_score or 0.0, 4)

    by_model_list = [
        {"model": m, **scores} for m, scores in by_model.items()
    ]

    # 5. Per-type hourly trend (separate series for each eval type)
    type_trend_rows = (
        session.query(
            hour_expr.label("hour"),
            EvalResult.eval_type,
            func.avg(EvalResult.score).label("avg_score"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .group_by(hour_expr, EvalResult.eval_type)
        .order_by(hour_expr.asc())
    )
    if start:
        type_trend_rows = type_trend_rows.filter(Completion.timestamp >= start)
    if end:
        type_trend_rows = type_trend_rows.filter(Completion.timestamp <= end)

    # Pivot trend by hour: [{hour, bleu, rouge, llm_judge, ...}]
    trend_pivot: dict = {}
    for r in type_trend_rows.all():
        h = str(r.hour)
        trend_pivot.setdefault(h, {"hour": h})[r.eval_type] = round(r.avg_score or 0.0, 4)
    trend_by_type = sorted(trend_pivot.values(), key=lambda x: x["hour"])

    # 6. Overall avg
    overall_avg = round(sum(all_scores) / len(all_scores), 4) if all_scores else None

    # 7. Win-rate per model (from human_preference evals: score==1.0 = win, 0.5 = tie, 0.0 = loss)
    hp_rows = (
        session.query(
            Completion.model,
            func.count(EvalResult.id).label("battles"),
            func.sum(case((EvalResult.score == 1.0, 1), else_=0)).label("wins"),
            func.sum(case((EvalResult.score == 0.5, 1), else_=0)).label("ties"),
            func.sum(case((EvalResult.score == 0.0, 1), else_=0)).label("losses"),
        )
        .join(Completion, EvalResult.completion_id == Completion.id)
        .filter(EvalResult.eval_type == "human_preference")
        .group_by(Completion.model)
        .order_by(func.avg(EvalResult.score).desc())
    )
    if start:
        hp_rows = hp_rows.filter(Completion.timestamp >= start)
    if end:
        hp_rows = hp_rows.filter(Completion.timestamp <= end)

    win_rates = [
        {
            "model": r.model,
            "battles": r.battles,
            "wins": r.wins,
            "ties": r.ties,
            "losses": r.losses,
            "win_rate": round(r.wins / r.battles, 4) if r.battles else 0.0,
            "win_tie_rate": round((r.wins + r.ties * 0.5) / r.battles, 4) if r.battles else 0.0,
        }
        for r in hp_rows.all()
    ]

    return {
        "total_evals": len(all_scores),
        "overall_avg_score": overall_avg,
        "by_type": by_type,
        "by_model": by_model_list,
        "distribution": buckets,
        "trend": trend,
        "trend_by_type": trend_by_type,
        "win_rates": win_rates,
    }
