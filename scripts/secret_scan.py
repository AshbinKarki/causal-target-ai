"""Focused offline secret-pattern scan of publishable files (not a full DLP audit)."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "github_token": r"gh[pousr]_[A-Za-z0-9]{30,}",
    "github_pat": r"github_pat_[A-Za-z0-9_]{50,}",
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "openai_token": r"sk-(?:proj-)?[A-Za-z0-9_-]{40,}",
}


def main():
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    failures = []
    for relative in set(paths):
        path = ROOT / relative
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".parquet"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS.items():
            if re.search(pattern, content):
                failures.append(f"{relative}: potential {name}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"No configured secret patterns found in {len(set(paths))} publishable files.")


if __name__ == "__main__":
    main()
