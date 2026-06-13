"""
Data seeder: loads LMSYS-style CSV and inserts completions into the database.

Usage:
    python backend/seed_data.py \\
        --csv-path backend/data/lmsys_sample.csv \\
        --rows 5000 \\
        --db sqlite:///./llm_obs.db
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import List

import pandas as pd

# Allow running as "python backend/seed_data.py" from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Completion
from backend.utils.helpers import estimate_tokens, calculate_cost, parse_iso_date

USERS = [f"user_{i:03d}" for i in range(1, 16)]  # 15 synthetic users

# Latency ranges (ms) per model family
_LATENCY: dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet":  (300, 800),
    "claude-3-opus":      (400, 900),
    "gpt-4":              (250, 600),
    "gpt-4-turbo":        (280, 650),
    "gpt-3.5-turbo":      (150, 500),
    "llama-2-70b":        (600, 2000),
    "mistral-large":      (500, 1500),
    "gemini-pro":         (300, 800),
    "palm-2":             (350, 900),
    "davinci-003":        (200, 700),
}

_NOW = datetime.now(timezone.utc)


class DataSeeder:
    BATCH_SIZE = 500

    def __init__(self, db_url: str):
        engine = create_engine(db_url, pool_pre_ping=True)
        Base.metadata.create_all(bind=engine)
        self._Session = sessionmaker(bind=engine)
        self._seen_convs: set[str] = set()

    # ------------------------------------------------------------------
    def load_csv(self, path: str, rows: int = 5000) -> pd.DataFrame:
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        df = pd.read_csv(path, nrows=rows)
        print(f"Loaded {len(df)} rows from {path}")
        return df

    # ------------------------------------------------------------------
    @staticmethod
    def generate_latency(model: str) -> float:
        lo, hi = _LATENCY.get(model.lower(), (500, 2000))
        return round(random.uniform(lo, hi), 1)

    # ------------------------------------------------------------------
    def _row_to_completion(self, row: pd.Series, idx: int) -> Completion | None:
        conv_id = str(row.get("conversation_id", f"conv_{idx}"))
        if conv_id in self._seen_convs:
            return None
        self._seen_convs.add(conv_id)

        # Pick one model from the pair
        model = str(row.get("model_a", "gpt-4")) if random.random() < 0.5 else str(row.get("model_b", "gpt-4"))

        # Use CSV token counts if present; otherwise estimate from a placeholder
        tokens_in = int(row["tokens_in"]) if "tokens_in" in row and pd.notna(row["tokens_in"]) else random.randint(50, 500)
        tokens_out = int(row["tokens_out"]) if "tokens_out" in row and pd.notna(row["tokens_out"]) else random.randint(20, 300)

        # Latency: prefer CSV value, else generate synthetically
        if "latency_ms" in row and pd.notna(row["latency_ms"]):
            latency = float(row["latency_ms"])
        else:
            latency = self.generate_latency(model)

        # Cost: prefer CSV value, else calculate
        if "cost_usd" in row and pd.notna(row["cost_usd"]):
            cost = float(row["cost_usd"])
        else:
            cost = calculate_cost(tokens_in, tokens_out, model)

        # Timestamp: spread across last 7 days if CSV value is too old or missing
        if "timestamp" in row and pd.notna(row["timestamp"]):
            try:
                ts = parse_iso_date(str(row["timestamp"]))
                # Make timezone-aware if naive
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = _NOW - timedelta(seconds=random.randint(0, 7 * 86400))
        else:
            ts = _NOW - timedelta(seconds=random.randint(0, 7 * 86400))

        prompt = f"[Conv {conv_id}] User prompt"
        response = f"[Model {model}] Response to conversation {conv_id}"

        return Completion(
            prompt=prompt,
            response=response,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency,
            cost_usd=cost,
            user_id=random.choice(USERS),
            conversation_id=conv_id,
            timestamp=ts.replace(tzinfo=None),  # store as naive UTC
        )

    # ------------------------------------------------------------------
    def seed(self, df: pd.DataFrame) -> int:
        total = len(df)
        inserted = 0
        db = self._Session()

        try:
            batch: List[Completion] = []
            for idx, row in df.iterrows():
                obj = self._row_to_completion(row, int(str(idx)))
                if obj is None:
                    continue
                batch.append(obj)

                if len(batch) >= self.BATCH_SIZE:
                    db.add_all(batch)
                    db.commit()
                    inserted += len(batch)
                    print(f"Inserted {inserted}/{total}...")
                    batch = []

            if batch:
                db.add_all(batch)
                db.commit()
                inserted += len(batch)
                print(f"Inserted {inserted}/{total}...")
        except Exception as exc:
            db.rollback()
            print(f"ERROR during seed: {exc}")
            raise
        finally:
            db.close()

        return inserted

    # ------------------------------------------------------------------
    def verify(self) -> int:
        db = self._Session()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM completions")).scalar()
            return int(count)
        finally:
            db.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed LLM observability database")
    parser.add_argument(
        "--csv-path",
        default=os.path.join(os.path.dirname(__file__), "data", "lmsys_sample.csv"),
        help="Path to LMSYS-style CSV file",
    )
    parser.add_argument("--rows", type=int, default=5000, help="Number of rows to read")
    parser.add_argument(
        "--db",
        default=os.getenv("DATABASE_URL", "sqlite:///./llm_obs.db"),
        help="SQLAlchemy database URL",
    )
    args = parser.parse_args()

    try:
        seeder = DataSeeder(args.db)
    except Exception as exc:
        print(f"ERROR: Database connection failed: {exc}")
        sys.exit(1)

    try:
        df = seeder.load_csv(args.csv_path, rows=args.rows)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    inserted = seeder.seed(df)
    count = seeder.verify()
    print(f"\nSuccessfully seeded {inserted} completions")
    print(f"SELECT COUNT(*) FROM completions -> {count}")


if __name__ == "__main__":
    main()
