"""Eight functional analytics views backed by executed reports."""

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components.ui import COLORS, chart, header, kpis, money, note
from causal_target.optimization import STRATEGIES, allocate, compare


def overview(b, folder):
    s, exp = b["summary"], b["summary"]["experiment"]
    header(
        "Decisions that make a difference.",
        "Measure incremental impact. Allocate with intent. Keep uncertainty in view.",
        "Executive overview",
    )
    st.markdown(
        '<div class="hero"><div class="eyebrow" style="color:#bdb0ee">CAUSAL INTELLIGENCE</div><h2>Find the customers your campaign can move.</h2><p>Purchase propensity tells you who may convert. Uplift estimates whose conversion probability changes when you intervene.</p></div>',
        unsafe_allow_html=True,
    )
    kpis(
        [
            (
                "OBSERVATIONS ANALYZED",
                f"{s['data']['rows_retained']:,}",
                "Uniform sample · corrected release",
            ),
            (
                "CONTROL CONVERSION",
                f"{exp['control_rate']:.3%}",
                f"{exp['control_events']:,} conversion events",
            ),
            (
                "TREATMENT CONVERSION",
                f"{exp['treatment_rate']:.3%}",
                "Assignment, not advertising exposure",
            ),
            (
                "AVERAGE TREATMENT EFFECT",
                f"{exp['ate'] * 100:+.3f} pp",
                f"95% CI [{exp['ci_low'] * 100:.3f}, {exp['ci_high'] * 100:.3f}] pp",
            ),
        ]
    )
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        st.subheader("Targeting performance")
        st.caption("Held-out cumulative incremental conversions · Horvitz–Thompson estimate")
        curves = b["uplift_curves"]
        chosen = [s["selected_causal"], "Predictive targeting", "Random targeting"]
        chart(
            px.line(
                curves[curves.model.isin(chosen)],
                x="fraction",
                y="incremental_conversions",
                color="model",
                labels={
                    "fraction": "Share of cohort targeted",
                    "incremental_conversions": "Incremental conversions",
                    "model": "",
                },
            )
        )
    with right:
        st.subheader("Decision brief")
        st.markdown(f"**{s['selected_causal']}** is the validation-selected causal model.")
        st.caption(
            "Selection: lower confidence bound on DR policy gain at the configured targeting capacity."
        )
        test = b["causal_test"].set_index("model").loc[s["selected_causal"]]
        note(
            f"At {test.targeted_fraction:.0%} targeting, held-out DR gain is <b>{test.dr_incremental_conversions:,.1f} conversions</b>. The 95% interval per customer is [{test.dr_ci_low:.5f}, {test.dr_ci_high:.5f}]."
        )
        st.markdown("**Recommended next step**")
        st.write(
            "Validate the targeting policy in a fresh randomized campaign with measured margins and costs. The benchmark alone does not justify a revenue claim."
        )
    st.divider()
    st.subheader("Financial scenario")
    st.caption(
        "Default configurable assumptions. Open Budget simulator to change costs, contribution value and capacity."
    )
    strategy = b["strategies"]
    row = strategy[strategy.strategy == "Profit optimized"].iloc[0]
    kpis(
        [
            (
                "MODEL-BASED INCREMENTAL CONVERSIONS",
                f"{row.incremental_conversions:,.1f}",
                "Estimated from CATE; not observed outcomes",
            ),
            (
                "SIMULATED INCREMENTAL PROFIT",
                money(row.incremental_profit),
                "Contribution value less intervention spend",
            ),
            (
                "MARKETING SPEND",
                money(row.spend),
                f"{row.budget_utilization:.1%} of configured budget",
            ),
        ]
    )
    chart(
        px.bar(
            strategy[strategy.feasible],
            y="strategy",
            x="incremental_profit",
            orientation="h",
            labels={"strategy": "", "incremental_profit": "Simulated incremental profit ($)"},
            color_discrete_sequence=[COLORS[1]],
        ),
        height=330,
    )


def explorer(b, folder):
    header(
        "Understand the evidence.",
        "Explore anonymized baseline features and experimental assignments.",
        "Data explorer",
    )
    s, quality = b["summary"], b["summary"]["quality"]
    kpis(
        [
            (
                "RETAINED ROWS",
                f"{quality['rows']:,}",
                f"{s['data']['source_rows_scanned']:,} source rows scanned",
            ),
            ("BASELINE FEATURES", "12", "f0 through f11 · anonymized"),
            (
                "MISSING VALUES",
                str(sum(quality["missing"].values())),
                "Strict finite-value validation",
            ),
            ("TREATMENT SHARE", f"{quality['treatment_share']:.2%}", "Released sample allocation"),
        ]
    )
    c1, c2 = st.columns(2)
    feature = c1.selectbox("Feature", [f"f{i}" for i in range(12)])
    arm = c2.selectbox("Assignment group", ["Both arms", "Control", "Treatment"])
    hist = b["feature_histograms"].query("feature == @feature").copy()
    if arm != "Both arms":
        hist = hist[hist.treatment == int(arm == "Treatment")]
    lower, upper = float(hist.left.min()), float(hist.right.max())
    bounds = st.slider("Displayed feature range (precomputed bins)", lower, upper, (lower, upper))
    hist = hist[(hist.right >= bounds[0]) & (hist.left <= bounds[1])]
    hist["midpoint"] = (hist.left + hist.right) / 2
    hist["assignment"] = hist.treatment.map({0: "Control", 1: "Treatment"})
    hist["share"] = hist["count"] / hist.groupby("assignment")["count"].transform("sum")
    chart(
        px.bar(
            hist,
            x="midpoint",
            y="share",
            color="assignment",
            barmode="overlay",
            opacity=0.65,
            labels={"midpoint": feature, "share": "Share within displayed bins", "assignment": ""},
        ),
        height=400,
    )
    st.caption(
        "Filters operate on saved histogram bins; boundary bins are included in full. Original feature rows are not redistributed with the dashboard."
    )
    tab1, tab2, tab3 = st.tabs(["Feature profile", "Correlations", "Data quality"])
    with tab1:
        st.dataframe(b["feature_summary"], hide_index=True, width="stretch")
    with tab2:
        corr = b["correlations"].set_index("feature")
        chart(
            px.imshow(corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto"),
            height=600,
        )
        st.caption(
            "Relationships with exposure and visit are descriptive. Both fields are excluded from prediction."
        )
    with tab3:
        st.json(quality)
        note(
            "Matching anonymized rows are retained. A repeated feature vector does not establish a duplicate person or event."
        )


def experimentation(b, folder):
    header(
        "Separate signal from uncertainty.",
        "Intention-to-treat analysis of assignment in the released benchmark.",
        "A/B experimentation",
    )
    exp = b["summary"]["experiment"]
    kpis(
        [
            ("ABSOLUTE LIFT", f"{exp['ate'] * 100:.3f} pp", "Treatment minus control"),
            (
                "RELATIVE LIFT",
                f"{exp['relative_lift']:.1%}" if exp["relative_lift"] is not None else "Undefined",
                "Relative to control conversion",
            ),
            ("TWO-SIDED P-VALUE", f"{exp['p_value']:.3g}", "Two-proportion Z-test"),
            (
                "PRACTICAL SIGNIFICANCE",
                "Supported" if exp["practically_positive"] else "Not established",
                "95% lower bound exceeds +0.1 pp",
            ),
        ]
    )
    a, c = st.columns(2, gap="large")
    with a:
        fig = go.Figure(
            go.Bar(
                x=["Control", "Treatment"],
                y=[exp["control_rate"], exp["treatment_rate"]],
                marker_color=[COLORS[5], COLORS[0]],
            )
        )
        fig.update_yaxes(tickformat=".2%", title="Conversion rate")
        chart(fig, "Conversion by assignment")
        st.dataframe(
            pd.DataFrame(
                {
                    "Arm": ["Control", "Treatment"],
                    "Observations": [exp["control_n"], exp["treatment_n"]],
                    "Conversions": [exp["control_events"], exp["treatment_events"]],
                }
            ),
            hide_index=True,
            width="stretch",
        )
    with c:
        fig = go.Figure(
            go.Scatter(
                x=[exp["ate"]],
                y=["ITT effect"],
                mode="markers",
                marker=dict(size=14),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=[exp["ci_high"] - exp["ate"]],
                    arrayminus=[exp["ate"] - exp["ci_low"]],
                ),
            )
        )
        fig.add_vline(x=0, line_dash="dash", line_color=COLORS[5])
        fig.update_xaxes(tickformat=".2%", title="Probability difference")
        chart(fig, "95% Newcombe–Wilson interval", height=230)
        note(
            f"At a +0.1 percentage-point minimum detectable effect, estimated prospective power is <b>{exp['planned_power_at_mde']:.1%}</b>. The approximate total sample required for 80% power is <b>{exp['required_total_n_80pct_power']:,}</b>, preserving this allocation ratio."
        )
    st.subheader("Randomization diagnostics")
    chart(
        px.bar(
            b["balance"],
            x="smd",
            y="feature",
            orientation="h",
            labels={"smd": "Standardized mean difference", "feature": ""},
        )
    )
    st.caption(
        f"Assignment-prediction held-out AUC: {b['summary']['causal_diagnostics']['assignment_test_auc']:.3f}. Predictability is a diagnostic, not proof of the randomization mechanism."
    )
    with st.expander("Full statistical results"):
        st.json(exp)
    note(
        "This is an assignment effect, not the effect of actually seeing an ad. Privacy sampling obscures the original campaign's effect; statistical significance here does not establish production profitability."
    )


def predictive(b, folder):
    header(
        "Who is likely to convert?",
        "Predictive baselines provide the comparison causal targeting must earn.",
        "Predictive machine learning",
    )
    st.dataframe(
        b["predictive_test"].drop(columns="confusion_matrix"), hide_index=True, width="stretch"
    )
    st.caption(
        f"Selected on validation average precision: {b['summary']['selected_predictive']}. Classification thresholds maximize validation F1; probability calibration uses a separate partition."
    )
    selected = st.multiselect(
        "Compare models", list(b["predictive_curves"]), default=list(b["predictive_curves"])
    )
    tabs = st.tabs(["ROC", "Precision–recall", "Calibration", "Confusion matrix", "Explainability"])
    for tab, kind, xlabel, ylabel in zip(
        tabs[:3],
        ["roc", "pr", "calibration"],
        ["False positive rate", "Recall", "Predicted probability"],
        ["True positive rate", "Precision", "Observed frequency"],
        strict=True,
    ):
        with tab:
            fig = go.Figure()
            for name in selected:
                curve = b["predictive_curves"][name][kind]
                fig.add_scatter(
                    x=curve["x"],
                    y=curve["y"],
                    name=name,
                    mode="lines+markers" if kind == "calibration" else "lines",
                )
            fig.update_xaxes(title=xlabel)
            fig.update_yaxes(title=ylabel)
            chart(fig, height=450)
    with tabs[3]:
        model = st.selectbox("Confusion matrix model", list(b["predictive_curves"]))
        matrix = ast.literal_eval(
            b["predictive_test"].set_index("model").loc[model, "confusion_matrix"]
        )
        chart(
            px.imshow(
                matrix,
                x=["Predicted no", "Predicted yes"],
                y=["Actual no", "Actual yes"],
                text_auto=True,
                color_continuous_scale="Purples",
            ),
            height=400,
        )
    with tabs[4]:
        chart(
            px.bar(
                b["shap_importance"].sort_values("mean_abs_shap"),
                x="mean_abs_shap",
                y="feature",
                orientation="h",
                labels={"mean_abs_shap": "Mean |SHAP| (uncalibrated log odds)", "feature": ""},
            )
        )
        for filename in ["shap_summary.png", "shap_dependence.png"]:
            path = folder / "figures" / filename
            if path.exists():
                st.image(str(path), width="stretch")
        note(
            "SHAP explains the predictive LightGBM model's uncalibrated log odds. It is neither a treatment-effect explanation nor evidence that a feature causes conversion."
        )


def causal(b, folder):
    header(
        "Who changes because of treatment?",
        "Compare treatment-effect rankings on untouched experimental observations.",
        "Causal AI & uplift",
    )
    metrics = b["causal_test"]
    paired = b["summary"].get("paired_policy_comparisons", [])
    if paired:
        comparison = paired[0]
        note(
            f"At the configured targeting capacity, the selected causal policy differs from predictive targeting by <b>{comparison['difference_conversions']:+.1f} estimated conversions</b> (paired 95% CI {comparison['conversions_ci_low']:+.1f} to {comparison['conversions_ci_high']:+.1f}). This run does not establish causal-model superiority over predictive targeting."
        )
    st.dataframe(
        metrics[
            [
                "model",
                "qini",
                "auuc",
                "dr_incremental_conversions",
                "bootstrap_ci_low",
                "bootstrap_ci_high",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Bootstrap bounds are incremental conversion probability per member of the full evaluation cohort at the fixed targeting capacity; not individual confidence intervals."
    )
    selected = st.multiselect(
        "Policies to display", metrics.model.tolist(), default=metrics.model.tolist()
    )
    curve_kind = st.radio("Curve", ["Uplift", "Qini"], horizontal=True)
    curves = b["uplift_curves"]
    chart(
        px.line(
            curves[curves.model.isin(selected)],
            x="fraction",
            y="incremental_conversions" if curve_kind == "Uplift" else "qini_gain",
            color="model",
            labels={"fraction": "Share targeted", "model": ""},
        ),
        height=450,
    )
    left, right = st.columns(2)
    with left:
        chart(
            px.histogram(b["targeting"], x="cate", nbins=50, labels={"cate": "Estimated CATE"}),
            "Selected model effect distribution",
        )
    with right:
        groups = b["subgroups"].copy()
        groups["error_plus"] = groups.ci_high - groups.dr_effect
        groups["error_minus"] = groups.dr_effect - groups.ci_low
        chart(
            px.scatter(
                groups,
                x="decile",
                y="dr_effect",
                error_y="error_plus",
                error_y_minus="error_minus",
                labels={"decile": "Predicted-effect decile", "dr_effect": "DR effect"},
            ),
            "Subgroup effects · 95% intervals",
        )
    with st.expander("Validation selection, stability and assumptions"):
        st.dataframe(b["causal_validation"], hide_index=True)
        st.dataframe(
            b["stability"][["model", "half", "qini", "dr_ci_low", "dr_ci_high"]], hide_index=True
        )
        st.json(b["summary"]["causal_diagnostics"])
    note(
        "CATE is an estimated conditional average difference. Individual counterfactual outcomes are unobserved. Intervals condition on fitted models and the propensity assumption; privacy sampling, training uncertainty and model selection are outside these intervals."
    )


def simulator(b, folder):
    header(
        "Make the budget work harder.",
        "Explore a financial scenario using real model scores and explicit economic assumptions.",
        "Marketing budget simulator",
    )
    scores = b["targeting"]
    cfg = b["summary"]["config"]
    controls, result = st.columns([1, 2.3], gap="large")
    with controls:
        st.subheader("Scenario inputs")
        budget = st.number_input(
            "Marketing budget ($)", 0.0, 1000000.0, float(cfg["budget"]), 100.0
        )
        cost = st.number_input(
            "Cost per intervention ($)",
            0.001,
            1000.0,
            float(cfg["intervention_cost"]),
            0.01,
            format="%.3f",
        )
        value = st.number_input(
            "Contribution per conversion ($)", 0.0, 100000.0, float(cfg["conversion_value"]), 5.0
        )
        capacity = (
            st.slider("Maximum targeting capacity (%)", 0, 100, int(cfg["capacity_fraction"] * 100))
            / 100
        )
        effect_scale = st.slider("Treatment-effect assumption (%)", 0, 150, 100, 5) / 100
        strategy = st.selectbox("Targeting strategy", STRATEGIES, index=5)
        st.caption(
            "All financial inputs are assumptions. Contribution is value after product costs, before marketing spend."
        )
    cate = scores.cate.to_numpy() * effect_scale
    chosen, metrics = allocate(cate, scores.probability, budget, cost, value, capacity, strategy)
    comparisons = compare(
        cate, scores.probability, budget=budget, cost=cost, value=value, capacity_fraction=capacity
    )
    with result:
        if not metrics["feasible"]:
            st.warning(
                "Treat everyone is infeasible under this budget or capacity. Increase both limits to cover the cohort."
            )
        kpis(
            [
                (
                    "CUSTOMERS TARGETED",
                    f"{metrics['targeted']:,}",
                    f"of {len(scores):,} scored observations",
                ),
                (
                    "EXPECTED INCREMENTAL CONVERSIONS",
                    f"{metrics['incremental_conversions']:,.1f}",
                    "Model-based estimate",
                ),
            ]
        )
        kpis(
            [
                (
                    "SIMULATED INCREMENTAL PROFIT",
                    money(metrics["incremental_profit"]),
                    f"Spend: {money(metrics['spend'])}",
                ),
                (
                    "BUDGET UTILIZATION",
                    f"{metrics['budget_utilization']:.1%}",
                    f"Unspent: {money(metrics['unspent_budget'])}",
                ),
            ]
        )
        st.metric(
            "Estimated marketing ROI",
            f"{metrics['roi']:.1%}" if metrics["roi"] is not None else "Undefined · no spending",
        )
        chart(
            px.bar(
                comparisons[comparisons.feasible],
                x="incremental_profit",
                y="strategy",
                orientation="h",
                labels={"incremental_profit": "Simulated incremental profit ($)", "strategy": ""},
                color_discrete_sequence=[COLORS[1]],
            ),
            height=340,
        )
    with st.expander("Scenario comparison and budget sensitivity", expanded=True):
        st.dataframe(comparisons.drop(columns="financial_basis"), hide_index=True, width="stretch")
        budget_grid = np.linspace(0, max(budget * 2, cost * len(scores) * 0.2), 21)
        grid = pd.DataFrame(
            [
                {
                    "budget": amount,
                    **allocate(cate, scores.probability, amount, cost, value, capacity)[1],
                }
                for amount in budget_grid
            ]
        )
        chart(
            px.line(
                grid,
                x="budget",
                y="incremental_profit",
                labels={"budget": "Budget ($)", "incremental_profit": "Simulated profit ($)"},
            ),
            height=300,
        )
    export = scores.assign(
        adjusted_cate=cate, incremental_value=cate * value - cost, recommended=chosen
    )
    st.download_button(
        "Export scenario recommendations",
        export.to_csv(index=False),
        "causal-target-scenario.csv",
        "text/csv",
    )
    note(
        "Equal intervention costs make score sorting an exact solution to the configured allocation problem. Profit optimization leaves budget unspent when the next treatment has nonpositive expected value. This is simulated profit, not realized company revenue."
    )
    st.caption(
        "Derived from Criteo v2.1 · Diemert et al. (2018) · exports remain subject to CC BY-NC-SA 4.0."
    )


def recommendations(b, folder):
    header(
        "Turn scores into a targeting list.",
        "Anonymous source-row identifiers. Review estimates before making a campaign decision.",
        "Customer recommendations",
    )
    cfg = b["summary"]["config"]
    scores = b["targeting"].copy()
    chosen, _ = allocate(
        scores.cate,
        scores.probability,
        cfg["budget"],
        cfg["intervention_cost"],
        cfg["conversion_value"],
        cfg["capacity_fraction"],
    )
    scores["incremental_value"] = scores.cate * cfg["conversion_value"] - cfg["intervention_cost"]
    scores["recommended"] = chosen
    c1, c2, c3 = st.columns(3)
    decision = c1.selectbox(
        "Decision", ["All observations", "Recommend intervention", "No intervention"]
    )
    minimum = c2.number_input(
        "Minimum estimated incremental value ($)",
        value=float(scores.incremental_value.min()),
        step=0.05,
    )
    order = c3.selectbox("Sort by", ["cate", "probability", "incremental_value", "observation_id"])
    if decision != "All observations":
        scores = scores[scores.recommended == (decision == "Recommend intervention")]
    scores = scores[scores.incremental_value >= minimum].sort_values(order, ascending=False)
    st.caption(
        f"{len(scores):,} matching observations · recommendations use the default scenario. Use Budget simulator for custom scenario exports."
    )
    if scores.empty:
        st.info(
            "No observations match these filters. Lower the minimum value or change the decision filter."
        )
    else:
        st.dataframe(scores.head(1000), hide_index=True, width="stretch", height=520)
        st.caption(
            "Table shows at most 1,000 rows; CSV includes every matching row. Column headers also support sorting."
        )
    st.download_button(
        "Download filtered recommendations",
        scores.to_csv(index=False),
        "causal-target-recommendations.csv",
        "text/csv",
    )
    if "cate_ci_low" not in scores:
        st.info(
            "The selected learner does not provide validated individual CATE intervals. Subgroup and policy uncertainty are available on Causal AI & uplift."
        )
    note(
        "Identifiers refer to anonymous positions in the source file and cannot be used to contact real customers. Predictions are experimental decision support, not observed individual treatment effects."
    )
    st.caption(
        "Criteo v2.1 · Diemert et al. (2018) · CC BY-NC-SA 4.0 applies to derived exports; noncommercial use with attribution and share-alike terms."
    )


def methodology(b, folder):
    header(
        "Built to be inspected.",
        "Provenance, methodology, assumptions and operating boundaries.",
        "Methodology & documentation",
    )
    st.markdown("""### Business question
    Which eligible observations have positive expected incremental contribution from intervention?

    ### System architecture
    Official Criteo archive → checksum and schema validation → uniform reservoir sample → Parquet + DuckDB → independent training / calibration / selection / test partitions → prediction + causal learners → held-out policy evaluation → budget optimization → precomputed dashboard.

    ### Identification and evaluation
    The estimand is τ(x) = E[Y(1) − Y(0) | X=x] in the released benchmark. Analysis assumes consistency, no interference, overlap and treatment exchangeability in this release. The original trial's design probability is unavailable; a training-only constant assignment fraction is used by default, with an explicit configuration override for a known design probability.

    S-, T-, X- and cross-fitted DR learners are compared with Causal Forest DML where enabled. No individual counterfactual is observed. Selection uses validation evidence; final metrics use untouched test outcomes. Doubly robust estimates combine outcome regressions with assignment weights. AUUC and Qini definitions and bootstrap limits appear in the evaluation report.

    ### Data limitations and ethics
    The corrected release removes the original advertiser-related leakage issue, but privacy sampling obscures original campaign lift. Features are anonymized projections. Exposure is post-treatment and visit is another outcome; both are excluded from predictors. No demographic meaning, fairness guarantee, user identity or actual financial return can be inferred. Deployment in a real campaign requires current consent, eligibility, representative randomized evidence and fairness review.

    ### Reproduction and deployment
    The app reads precomputed reports and never trains models on startup. See the repository README and deployment guide for uv, Docker, MLflow and batch inference commands. Python model artifacts are trusted-local files and are never deserialized from dashboard uploads.
    """)
    st.link_button(
        "Criteo dataset and terms", "https://ailab.criteo.com/criteo-uplift-prediction-dataset/"
    )
    st.link_button(
        "Official corrected release", "https://huggingface.co/datasets/criteo/criteo-uplift"
    )
    meta_path = Path(__file__).resolve().parents[1] / "docs/project-metadata.json"
    if meta_path.exists():
        import json

        meta = json.loads(meta_path.read_text())
        if meta.get("repository_url"):
            st.link_button("GitHub repository", meta["repository_url"])
    for filename, title in [
        ("experimentation.md", "Experimentation report"),
        ("model-evaluation.md", "Model evaluation report"),
        ("executive_summary/report.md", "Executive report"),
    ]:
        path = folder / filename
        if path.exists():
            with st.expander(title):
                st.markdown(path.read_text(encoding="utf-8"))
                st.download_button(
                    f"Download {title.lower()}",
                    path.read_text(encoding="utf-8"),
                    Path(filename).name,
                    "text/markdown",
                )
    with st.expander("Run provenance and monitoring"):
        st.json(b["summary"])
        st.dataframe(b["drift"], hide_index=True)
        st.caption(
            "Train-versus-test PSI and KS are baseline diagnostics; this is not a live production drift stream."
        )
    st.markdown(
        "**Author:** Ashbin Karki · Master's in Data Science and AI, specializing in Artificial Intelligence. Original code: MIT. Criteo data and derived artifacts: CC BY-NC-SA 4.0."
    )


VIEWS = {
    "Executive overview": overview,
    "Data explorer": explorer,
    "A/B experimentation": experimentation,
    "Predictive models": predictive,
    "Causal AI & uplift": causal,
    "Budget simulator": simulator,
    "Customer recommendations": recommendations,
    "Methodology & docs": methodology,
}
