"""Acquire the corrected release and sample uniformly across its complete stream."""

import gzip
import json
import logging
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from sklearn.model_selection import train_test_split

from causal_target.config import FEATURES, LABELS, Config
from causal_target.utils import json_write, now, sha256

SOURCE_URL = "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/82811785048bb633de2d55c02bab4e57066e6423/criteo-research-uplift-v2.1.csv.gz"
EXPECTED_SHA256 = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"
SOURCE_PAGE = "https://ailab.criteo.com/criteo-uplift-prediction-dataset/"
EXPECTED_ROWS = 13_979_592
DATA_LICENSE = "CC BY-NC-SA 4.0"
LOG = logging.getLogger(__name__)


def download(root: Path, expected_sha256: str | None = EXPECTED_SHA256) -> Path:
    """Atomic download; record SHA-256 and validate gzip CRC by reading to EOF."""
    folder = root / "data/raw"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "criteo-uplift-v2.1.csv.gz"
    manifest_path = folder / "download.json"
    if path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        actual = sha256(path)
        if actual != manifest["sha256"] or (expected_sha256 and actual != expected_sha256):
            raise ValueError("Cached archive checksum mismatch; preserve and investigate the file")
        return path
    partial = path.with_suffix(".gz.partial")
    LOG.info("Downloading corrected Criteo release")
    with requests.get(SOURCE_URL, stream=True, timeout=(30, 120)) as response:
        response.raise_for_status()
        length = int(response.headers.get("Content-Length", 0))
        with partial.open("wb") as out:
            for chunk in response.iter_content(4 * 1024 * 1024):
                out.write(chunk)
        if length and partial.stat().st_size != length:
            raise ValueError("Incomplete download")
        etag = response.headers.get("ETag")
    digest = sha256(partial)
    if expected_sha256 and digest != expected_sha256:
        raise ValueError("Downloaded archive does not match expected SHA-256")
    with gzip.open(partial, "rb") as stream:
        header = stream.readline().decode("utf-8").strip().split(",")
        if set(header) != set(FEATURES + LABELS):
            raise ValueError(f"Unexpected official schema: {header}")
        for _ in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            pass
    partial.replace(path)
    json_write(
        manifest_path,
        {
            "source": SOURCE_URL,
            "source_page": SOURCE_PAGE,
            "license": DATA_LICENSE,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "etag": etag,
            "gzip_crc_verified": True,
            "downloaded_at": now(),
            "upstream_checksum_available": True,
            "schema": header,
            "legacy_host_status": "Criteo Azure storage DNS unavailable on 2026-11-25; using Criteo-owned Hugging Face release",
        },
    )
    return path


def validate(frame: pd.DataFrame, require_both_arms: bool = True) -> dict:
    """Strict schema contract; matching feature rows are reported, never deleted."""
    if frame.empty:
        raise ValueError("Dataset is empty")
    missing = set(FEATURES + LABELS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    for name in FEATURES + LABELS:
        if not pd.api.types.is_numeric_dtype(frame[name]):
            raise ValueError(f"Non-numeric field: {name}")
        if not np.isfinite(frame[name].to_numpy()).all():
            raise ValueError(f"Missing or infinite values: {name}")
    for name in LABELS:
        if not frame[name].isin([0, 1]).all():
            raise ValueError(f"Nonbinary field: {name}")
    if require_both_arms and frame.treatment.nunique() != 2:
        raise ValueError("Both assignment arms are required")
    if "observation_id" in frame and frame.observation_id.duplicated().any():
        raise ValueError("Duplicate source row identifiers")
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "missing": frame.isna().sum().to_dict(),
        "matching_feature_rows": int(frame.duplicated(FEATURES).sum()),
        "matching_complete_rows": int(frame.duplicated(FEATURES + LABELS).sum()),
        "conversion_events": int(frame.conversion.sum()),
        "treatment_share": float(frame.treatment.mean()),
        "exposed_controls": int(((frame.treatment == 0) & (frame.exposure == 1)).sum()),
        "conversion_without_visit": int(((frame.conversion == 1) & (frame.visit == 0)).sum()),
    }


def ingest(root: Path, cfg: Config, archive: Path) -> Path:
    """Exact-size uniform priority reservoir, independent of treatment/outcome.

    Each row receives one seeded IID random priority. Keep the smallest K across
    every chunk. Full mode streams all records directly to Parquet.
    """
    folder = root / "data/processed" / cfg.profile
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "observations.parquet"
    manifest_path = folder / "manifest.json"
    digest = sha256(archive)
    if path.exists() and manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if (
            previous.get("archive_sha256") == digest
            and previous.get("sample_rows") == cfg.sample_rows
            and previous.get("seed") == cfg.seed
            and previous.get("parquet_sha256") == sha256(path)
        ):
            return path
    rng = np.random.default_rng(cfg.seed)
    reservoir = None
    count = 0
    writer = None
    temp = path.with_suffix(".partial.parquet")
    dtype = {f: "float32" for f in FEATURES} | {f: "int8" for f in LABELS}
    try:
        for chunk in pd.read_csv(archive, compression="gzip", chunksize=250000, dtype=dtype):
            validate(chunk, require_both_arms=False)
            chunk.insert(0, "observation_id", np.arange(count, count + len(chunk), dtype=np.int64))
            count += len(chunk)
            if cfg.sample_rows is None:
                table = pa.Table.from_pandas(chunk, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(temp, table.schema, compression="zstd")
                writer.write_table(table)
            else:
                chunk["_priority"] = rng.random(len(chunk))
                candidates = (
                    chunk if reservoir is None else pd.concat([reservoir, chunk], ignore_index=True)
                )
                if len(candidates) > cfg.sample_rows:
                    take = np.argpartition(candidates._priority.to_numpy(), cfg.sample_rows - 1)[
                        : cfg.sample_rows
                    ]
                    reservoir = candidates.iloc[take].copy()
                else:
                    reservoir = candidates
            if count % 2000000 == 0:
                LOG.info("Scanned %s source rows", count)
    finally:
        if writer is not None:
            writer.close()
    if count != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} corrected rows, found {count}")
    if reservoir is not None:
        reservoir.drop(columns="_priority").sort_values("observation_id").to_parquet(
            temp, index=False, compression="zstd"
        )
    temp.replace(path)
    json_write(
        manifest_path,
        {
            "source": SOURCE_URL,
            "source_page": SOURCE_PAGE,
            "license": DATA_LICENSE,
            "synthetic": False,
            "source_rows_scanned": count,
            "rows_retained": min(count, cfg.sample_rows or count),
            "sample_rows": cfg.sample_rows,
            "sampling": "Uniform fixed-size IID-priority reservoir across entire release"
            if cfg.sample_rows
            else "All rows",
            "seed": cfg.seed,
            "archive_sha256": digest,
            "parquet_sha256": sha256(path),
            "created_at": now(),
        },
    )
    return path


def synthetic(n: int = 20000, seed: int = 42) -> pd.DataFrame:
    """Explicit testing fixture with known CATE, not Criteo or portfolio evidence."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 12))
    t = rng.binomial(1, 0.7, n)
    mu0 = 0.08 + 0.12 / (1 + np.exp(-x[:, 1]))
    tau = np.where(x[:, 0] > 0, 0.12, -0.04)
    y = rng.binomial(1, mu0 + t * tau)
    frame = pd.DataFrame(x.astype("float32"), columns=FEATURES)
    frame["treatment"] = t
    frame["conversion"] = y
    frame["visit"] = np.maximum(y, rng.binomial(1, 0.4, n))
    frame["exposure"] = t * rng.binomial(1, 0.8, n)
    frame["observation_id"] = np.arange(n)
    frame["true_cate"] = tau
    return frame


def partition(frame: pd.DataFrame, seed: int) -> dict[str, pd.DataFrame]:
    """60/10/10/20 train/calibration/selection/test, stratified on T and Y."""
    strata = frame.treatment.astype(str) + frame.conversion.astype(str)
    if strata.value_counts().min() < 20:
        raise ValueError(
            "At least 20 rows in each treatment/outcome cell are needed; increase sample size"
        )

    def split(df, fraction, offset):
        return train_test_split(
            df,
            test_size=fraction,
            random_state=seed + offset,
            stratify=df.treatment.astype(str) + df.conversion.astype(str),
        )

    train, rest = split(frame, 0.4, 0)
    validation, test = split(rest, 0.5, 1)
    calibration, selection = split(validation, 0.5, 2)
    return dict(train=train, calibration=calibration, selection=selection, test=test)


def warehouse(root: Path, frame: pd.DataFrame, scores: pd.DataFrame | None = None):
    """Persist analytical tables and execute checked-in SQL reports."""
    folder = root / "data/processed"
    folder.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(folder / "analytics.duckdb"))
    con.register("input_observations", pl.from_pandas(frame).to_arrow())
    con.execute("CREATE OR REPLACE TABLE observations AS SELECT * FROM input_observations")
    if scores is not None:
        con.register("input_scores", scores)
        con.execute("CREATE OR REPLACE TABLE scores AS SELECT * FROM input_scores")
    for sql in sorted((root / "sql").glob("*.sql")):
        if "scores" in sql.read_text() and scores is None:
            continue
        result = con.execute(sql.read_text()).df()
        out = root / "reports/metrics/sql" / (sql.stem + ".csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out, index=False)
    con.close()
