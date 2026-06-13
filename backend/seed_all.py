"""
Dual-source database seeder.

Source 1 — LMSYS Chatbot Arena (lmsys_sample.csv)
  • Real conversations from Chatbot Arena (anonymised metadata)
  • source='lmsys', eval_type='human_preference' (winner field)
  • Use for: cost/latency analytics, model-vs-model win rates

Source 2 — Evals Benchmark (evals_dataset.csv)
  • Real prompt/response pairs with human quality ratings
  • source='evals_benchmark', eval_types: bleu, rouge, [llm_judge]
  • Use for: response quality benchmarking

These two sources are NEVER mixed in aggregate queries.

Usage (from project root):
    python backend/seed_all.py [--reset] [--no-llm-judge] [--judge-limit N]
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Completion, EvalResult
from backend.utils.helpers import calculate_cost, parse_iso_date

_NOW = datetime.now(timezone.utc)
USERS = [f"user_{i:03d}" for i in range(1, 21)]


def _ts(raw) -> datetime:
    try:
        ts = parse_iso_date(str(raw))
        return ts.replace(tzinfo=None) if ts.tzinfo else ts
    except Exception:
        return (_NOW - timedelta(seconds=random.randint(0, 7 * 86400))).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Source 1: LMSYS Chatbot Arena — real production metrics + human preference
# ---------------------------------------------------------------------------

def seed_lmsys(path: str, session_factory) -> dict:
    """
    Seed LMSYS arena data.

    Each CSV row = one arena battle (model_a vs model_b). We insert TWO
    completions (one per model) so per-model analytics work correctly.
    The winner field becomes a human_preference EvalResult score:
        model wins  → 1.0
        tie         → 0.5
        model loses → 0.0
    """
    df = pd.read_csv(path)
    print(f"[lmsys] {len(df)} rows loaded")

    db = session_factory()
    batch: list[tuple[Completion, float]] = []
    seen: set[str] = set()
    inserted = 0

    def _flush():
        nonlocal inserted
        comps = [c for c, _ in batch]
        db.add_all(comps)
        db.flush()
        for comp, score in batch:
            db.add(EvalResult(
                completion_id=comp.id,
                eval_type="human_preference",
                score=score,
                source="human_preference",
                explanation="LMSYS Chatbot Arena human judge",
            ))
        db.commit()
        inserted += len(batch)
        batch.clear()

    try:
        for _, row in df.iterrows():
            conv_id = str(row.get("conversation_id", f"lmsys_{_}"))
            if conv_id in seen:
                continue
            seen.add(conv_id)

            model_a = str(row["model_a"])
            model_b = str(row["model_b"])
            winner  = str(row.get("winner", "tie"))
            lang    = str(row.get("language", "English"))

            tokens_in  = int(row["tokens_in"])  if pd.notna(row.get("tokens_in"))  else random.randint(50, 500)
            tokens_out = int(row["tokens_out"]) if pd.notna(row.get("tokens_out")) else random.randint(20, 300)
            latency    = float(row["latency_ms"]) if pd.notna(row.get("latency_ms")) else 500.0
            cost       = float(row["cost_usd"])   if pd.notna(row.get("cost_usd"))   else calculate_cost(tokens_in, tokens_out, model_a)
            ts         = _ts(row.get("timestamp"))

            score_a = 1.0 if winner == "model_a" else (0.5 if winner == "tie" else 0.0)
            score_b = 1.0 if winner == "model_b" else (0.5 if winner == "tie" else 0.0)

            prompt   = f"[{lang}] Arena battle: {model_a} vs {model_b}"
            response = f"Winner: {winner}"

            batch.append((
                Completion(
                    prompt=prompt, response=response, model=model_a,
                    tokens_in=tokens_in, tokens_out=tokens_out,
                    latency_ms=latency, cost_usd=cost,
                    user_id=random.choice(USERS),
                    conversation_id=conv_id,
                    timestamp=ts,
                    source="lmsys",
                ),
                score_a,
            ))
            batch.append((
                Completion(
                    prompt=prompt, response=response, model=model_b,
                    tokens_in=tokens_in, tokens_out=tokens_out,
                    latency_ms=latency, cost_usd=cost * 0.8,
                    user_id=random.choice(USERS),
                    conversation_id=conv_id + "_b",
                    timestamp=ts,
                    source="lmsys",
                ),
                score_b,
            ))

            if len(batch) >= 500:
                _flush()
                print(f"  [lmsys] {inserted} completions…")

        if batch:
            _flush()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"[lmsys] done — {inserted} completions, {inserted} human_preference evals")
    return {"completions": inserted, "evals": inserted}


# ---------------------------------------------------------------------------
# Source 2: Evals Benchmark — real prompt/response, quality metrics
# ---------------------------------------------------------------------------

def seed_evals_benchmark(path: str, session_factory, run_llm_judge: bool = False, judge_limit: int = 20) -> dict:
    """
    Seed evaluation benchmark data.

    Each row has a real prompt + response pair. We compute BLEU, ROUGE,
    and optionally run the LLM judge. These are the ONLY completions on
    which quality-metric evals are meaningful.
    """
    from backend.evals.text_metrics import TextMetrics

    df = pd.read_csv(path)
    print(f"[evals_benchmark] {len(df)} rows loaded")

    db = session_factory()
    inserted_comps = 0
    inserted_evals = 0

    try:
        for i, row in df.iterrows():
            prompt      = str(row["prompt"])
            response    = str(row["response"])
            criteria    = str(row.get("criteria", "helpful, accurate, relevant"))
            human_score = float(row.get("quality_rating", 5)) / 10.0

            comp = Completion(
                prompt=prompt,
                response=response,
                model="eval-dataset",
                tokens_in=max(1, len(prompt.split())),
                tokens_out=max(1, len(response.split())),
                latency_ms=0.0,
                cost_usd=0.0,
                user_id="benchmark",
                timestamp=(_NOW - timedelta(hours=random.randint(0, 72))).replace(tzinfo=None),
                source="evals_benchmark",
            )
            db.add(comp)
            db.flush()

            # BLEU
            try:
                bleu = TextMetrics.bleu_score(prompt, response)
                db.add(EvalResult(completion_id=comp.id, eval_type="bleu", score=bleu, source="benchmark"))
                inserted_evals += 1
            except Exception as e:
                print(f"  bleu error row {i}: {e}")

            # ROUGE (rougeL as scalar)
            try:
                rouge_raw = TextMetrics.rouge_score(prompt, response)
                rouge = float(rouge_raw.get("rougeL", rouge_raw.get("rouge1", 0.0))) if isinstance(rouge_raw, dict) else float(rouge_raw)
                db.add(EvalResult(completion_id=comp.id, eval_type="rouge", score=rouge, source="benchmark"))
                inserted_evals += 1
            except Exception as e:
                print(f"  rouge error row {i}: {e}")

            # Human quality rating (already collected in CSV)
            db.add(EvalResult(
                completion_id=comp.id,
                eval_type="human",
                score=human_score,
                criteria=criteria,
                explanation=f"Rated by: {row.get('human_rater', '?')}",
                source="benchmark",
            ))
            inserted_evals += 1

            db.commit()
            inserted_comps += 1
            if (i + 1) % 25 == 0:
                print(f"  [evals_benchmark] {i + 1}/{len(df)} done")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # Optional LLM judge pass
    if run_llm_judge and judge_limit > 0:
        inserted_evals += _run_llm_judge(session_factory, limit=judge_limit)

    print(f"[evals_benchmark] done — {inserted_comps} completions, {inserted_evals} evals")
    return {"completions": inserted_comps, "evals": inserted_evals}


def _run_llm_judge(session_factory, limit: int = 20) -> int:
    """Run Azure OpenAI LLM judge only on evals_benchmark completions."""
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()

    db = session_factory()
    judge = LLMJudge()
    done = 0
    try:
        comps = (
            db.query(Completion)
            .filter(Completion.source == "evals_benchmark")
            .limit(limit)
            .all()
        )
        print(f"[llm_judge] scoring {len(comps)} benchmark completions with {judge._model}…")
        for comp in comps:
            already = db.query(EvalResult).filter(
                EvalResult.completion_id == comp.id,
                EvalResult.eval_type == "llm_judge",
            ).first()
            if already:
                continue
            try:
                score = judge.evaluate_response(comp.prompt, comp.response)
                explanation = judge.get_evaluation_explanation(comp.prompt, comp.response)
                db.add(EvalResult(
                    completion_id=comp.id,
                    eval_type="llm_judge",
                    score=score,
                    explanation=explanation[:500] if explanation else None,
                    source="benchmark",
                ))
                db.commit()
                done += 1
                print(f"  [{done}/{len(comps)}] id={comp.id} score={score:.2f}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  llm_judge error id={comp.id}: {e}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"[llm_judge] done — {done} completions judged")
    return done


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def seed_all(
    db_url: str = "sqlite:///./llm_obs.db",
    reset: bool = True,
    run_llm_judge: bool = False,
    judge_limit: int = 20,
) -> dict:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    if reset:
        print("Dropping all tables…")
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    print("\n=== SOURCE 1: LMSYS Chatbot Arena (production metrics + win rates) ===")
    lmsys_stats = seed_lmsys(os.path.join(data_dir, "lmsys_sample.csv"), Session)

    print("\n=== SOURCE 2: Evals Benchmark (response quality metrics) ===")
    bench_stats = seed_evals_benchmark(
        os.path.join(data_dir, "evals_dataset.csv"),
        Session,
        run_llm_judge=run_llm_judge,
        judge_limit=judge_limit,
    )

    with engine.connect() as c:
        total_comps  = c.execute(text("SELECT COUNT(*) FROM completions")).scalar()
        total_evals  = c.execute(text("SELECT COUNT(*) FROM eval_results")).scalar()
        by_source    = c.execute(text("SELECT source, COUNT(*) FROM completions GROUP BY source")).fetchall()
        by_eval_type = c.execute(text("SELECT eval_type, COUNT(*), ROUND(AVG(score),3) FROM eval_results GROUP BY eval_type")).fetchall()

    print(f"\n{'='*60}")
    print(f"Total completions : {total_comps}")
    print(f"Total eval results: {total_evals}")
    print("By completion source:")
    for src, n in by_source:
        print(f"  {src:<20} {n}")
    print("By eval type:")
    for et, n, avg in by_eval_type:
        print(f"  {et:<20} {n:>6}  avg={avg}")
    print(f"{'='*60}")

    return {
        "lmsys": lmsys_stats,
        "evals_benchmark": bench_stats,
        "total_completions": total_comps,
        "total_evals": total_evals,
    }


def main():
    parser = argparse.ArgumentParser(description="Dual-source DB seeder")
    parser.add_argument("--db", default="sqlite:///./llm_obs.db")
    parser.add_argument("--reset", action="store_true", default=True,
                        help="Drop and recreate tables before seeding (default: True)")
    parser.add_argument("--no-reset", dest="reset", action="store_false")
    parser.add_argument("--llm-judge", action="store_true",
                        help="Run LLM judge on evals_benchmark completions (needs Azure API key)")
    parser.add_argument("--judge-limit", type=int, default=20)
    args = parser.parse_args()

    seed_all(
        db_url=args.db,
        reset=args.reset,
        run_llm_judge=args.llm_judge,
        judge_limit=args.judge_limit,
    )


if __name__ == "__main__":
    main()
