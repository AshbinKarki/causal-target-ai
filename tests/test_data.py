import gzip
import json

import numpy as np
import pandas as pd
import pytest

from causal_target import data
from causal_target.config import FEATURES, LABELS, Config
from causal_target.data import ingest, partition, validate
from causal_target.predictive import features
from causal_target.utils import sha256


def test_schema_and_source_identity(sample):
    result = validate(sample)
    assert result["rows"] == len(sample)
    assert sum(result["missing"].values()) == 0
    duplicated = pd.concat([sample.iloc[:1], sample.iloc[:1]], ignore_index=True)
    duplicated.observation_id = [1, 2]
    assert validate(duplicated, require_both_arms=False)["matching_feature_rows"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "empty",
        "missing_column",
        "nan",
        "infinity",
        "string",
        "bad_arm",
        "single_arm",
        "repeated_id",
    ],
)
def test_invalid_schema_rejected(sample, mutation):
    frame = sample.copy()
    if mutation == "empty":
        frame = frame.iloc[:0]
    elif mutation == "missing_column":
        frame = frame.drop(columns="f1")
    elif mutation == "nan":
        frame.loc[0, "f1"] = np.nan
    elif mutation == "infinity":
        frame.loc[0, "f1"] = np.inf
    elif mutation == "string":
        frame["f1"] = "bad"
    elif mutation == "bad_arm":
        frame.loc[0, "treatment"] = 2
    elif mutation == "single_arm":
        frame["treatment"] = 1
    else:
        frame.loc[1, "observation_id"] = frame.loc[0, "observation_id"]
    with pytest.raises(ValueError):
        validate(frame)


def test_partitions_disjoint_complete_and_reproducible(sample):
    parts = partition(sample, 42)
    ids = [set(p.observation_id) for p in parts.values()]
    assert set.union(*ids) == set(sample.observation_id)
    assert sum(map(len, ids)) == len(set.union(*ids))
    assert [len(p) for p in parts.values()] == [3000, 500, 500, 1000]
    assert parts["test"].equals(partition(sample, 42)["test"])


def test_post_treatment_fields_cannot_enter_features(sample):
    a = features(sample)
    sample["exposure"] = 500
    sample["visit"] = 700
    sample["conversion"] = 42
    sample["true_cate"] = 8
    np.testing.assert_array_equal(features(sample), a)
    assert a.shape[1] == 12


def test_stream_sampling_integrity_and_cache(tmp_path, sample, monkeypatch):
    archive = tmp_path / "fixture.csv.gz"
    sample[FEATURES + LABELS].to_csv(archive, index=False, compression="gzip")
    monkeypatch.setattr(data, "EXPECTED_ROWS", len(sample))
    cfg = Config(sample_rows=1000)
    output = ingest(tmp_path, cfg, archive)
    frame = pd.read_parquet(output)
    assert len(frame) == 1000
    assert frame.observation_id.max() > 4500
    assert frame.observation_id.min() < 100
    assert frame.observation_id.nunique() == 1000
    manifest = json.loads(output.with_name("manifest.json").read_text())
    assert manifest["source_rows_scanned"] == 5000
    assert manifest["parquet_sha256"] == sha256(output)
    assert ingest(tmp_path, cfg, archive) == output
    with pytest.raises(ValueError, match="Expected"):
        monkeypatch.setattr(data, "EXPECTED_ROWS", 6000)
        ingest(tmp_path, Config(sample_rows=1100), archive)


def test_full_ingest_streams_every_row(tmp_path, sample, monkeypatch):
    archive = tmp_path / "fixture.csv.gz"
    sample[FEATURES + LABELS].to_csv(archive, index=False, compression="gzip")
    monkeypatch.setattr(data, "EXPECTED_ROWS", len(sample))
    output = ingest(tmp_path, Config(sample_rows=None), archive)
    assert len(pd.read_parquet(output)) == len(sample)


def test_download_verifies_checksum_and_archive(tmp_path, sample, monkeypatch):
    payload = gzip.compress(sample[FEATURES + LABELS].head(100).to_csv(index=False).encode())

    class Response:
        headers = {"Content-Length": str(len(payload)), "ETag": "test-etag"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield payload

    monkeypatch.setattr(data.requests, "get", lambda *args, **kwargs: Response())
    import hashlib

    checksum = hashlib.sha256(payload).hexdigest()
    path = data.download(tmp_path, checksum)
    assert path.read_bytes() == payload
    assert json.loads(path.with_name("download.json").read_text())["gzip_crc_verified"]
    path.write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        data.download(tmp_path, checksum)
