"""Create a vector portfolio card using an actual held-out uplift curve."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    frame = pd.read_csv(ROOT / "reports/metrics/uplift_curves.csv")
    curve = frame[frame.model == "DR-learner"]
    high = max(float(curve.incremental_conversions.max()), 1)
    points = " ".join(
        f"{720 + x * 360:.1f},{450 - y / high * 230:.1f}"
        for x, y in zip(curve.fraction, curve.incremental_conversions, strict=True)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title description">
<title id="title">CausalTarget AI portfolio project</title><desc id="description">Causal targeting, 500,000 real observations analyzed, five causal learners. Chart from actual held-out DR-learner uplift evaluation.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#201b36"/><stop offset="1" stop-color="#51408c"/></linearGradient></defs>
<rect width="1200" height="630" rx="24" fill="url(#bg)"/>
<rect x="65" y="65" width="57" height="57" rx="16" fill="#8975fa"/>
<path d="m94 76 17 18-17 17-17-17Z" fill="none" stroke="white" stroke-width="3"/>
<text x="145" y="102" fill="white" font-family="Arial,sans-serif" font-size="27" font-weight="bold">CausalTarget AI</text>
<text x="65" y="211" fill="#c3b8ef" font-family="Arial,sans-serif" font-size="14" letter-spacing="4">EVIDENCE BEFORE INTERVENTION</text>
<text x="65" y="282" fill="white" font-family="Arial,sans-serif" font-size="48" font-weight="bold">Who changes</text>
<text x="65" y="343" fill="white" font-family="Arial,sans-serif" font-size="48" font-weight="bold">because of treatment?</text>
<text x="65" y="396" fill="#ddd5f4" font-family="Arial,sans-serif" font-size="20">Causal inference. Policy evaluation. Budget decisions.</text>
<rect x="65" y="462" width="185" height="62" rx="13" fill="#ffffff" fill-opacity=".08"/>
<text x="83" y="489" fill="white" font-family="Arial,sans-serif" font-size="22" font-weight="bold">500,000</text>
<text x="83" y="509" fill="#cec3eb" font-family="Arial,sans-serif" font-size="12">REAL OBSERVATIONS ANALYZED</text>
<rect x="267" y="462" width="185" height="62" rx="13" fill="#ffffff" fill-opacity=".08"/>
<text x="285" y="489" fill="white" font-family="Arial,sans-serif" font-size="22" font-weight="bold">5 causal learners</text>
<text x="285" y="509" fill="#cec3eb" font-family="Arial,sans-serif" font-size="12">100,000 HELD-OUT ROWS</text>
<path d="M720 200V450H1080" fill="none" stroke="#bdb0df" stroke-opacity=".4"/>
<path d="M720 450 1080 220" fill="none" stroke="#bdb0df" stroke-dasharray="6 7" opacity=".5"/>
<polyline points="{points}" fill="none" stroke="#65dac4" stroke-width="4" stroke-linejoin="round"/>
<text x="720" y="494" fill="#ddd5f4" font-family="Arial,sans-serif" font-size="13">HELD-OUT UPLIFT · DR LEARNER</text>
<text x="65" y="582" fill="#c3b8ef" font-family="Arial,sans-serif" font-size="15">Ashbin Karki · Data Science portfolio</text>
<text x="720" y="582" fill="#c3b8ef" font-family="Arial,sans-serif" font-size="11">Criteo v2.1 · Benchmark, not realized revenue</text>
</svg>'''
    (ROOT / "docs/assets/project-thumbnail.svg").write_text(svg, encoding="utf-8")
    print("Created data-backed SVG portfolio thumbnail")


if __name__ == "__main__":
    main()
