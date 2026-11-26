"""Consistent visual language and accessible chart defaults."""

import plotly.graph_objects as go
import streamlit as st

COLORS = ["#7463ed", "#16a994", "#efad55", "#df6984", "#4b93e0", "#96a0b7", "#ba76d9"]


def theme():
    st.markdown(
        """<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    html, body, [class*='css'], .stApp {font-family: 'DM Sans', sans-serif;}
    h1,h2,h3 {font-family:'Manrope',sans-serif;letter-spacing:-.04em;}
    h1 {font-weight:800!important;font-size:2.4rem!important;padding-top:.25rem!important;}
    .block-container {max-width:1480px;padding:4rem 3rem 3rem;}
    [data-testid='stSidebar'] {border-right:1px solid rgba(128,128,128,.14);}
    [data-testid='stSidebar'] .block-container {padding-top:2rem;}
    [data-testid='stMetric'] {border:1px solid rgba(128,128,128,.18);border-radius:14px;padding:20px 22px;background:rgba(128,128,128,.025);}
    [data-testid='stMetricLabel'] {font-size:.79rem;letter-spacing:.02em;}
    [data-testid='stMetricValue'] {font-family:'Manrope',sans-serif;font-size:1.85rem;font-weight:800;}
    .eyebrow {font-size:.70rem;font-weight:700;letter-spacing:.14em;color:#8c89a0;text-transform:uppercase;margin-bottom:8px;}
    .brand {font-family:'Manrope',sans-serif;font-size:1.35rem;font-weight:800;letter-spacing:-.06em;display:flex;align-items:center;gap:9px;margin-bottom:4px;}
    .brand-icon {background:#7463ed;color:white;border-radius:10px;padding:6px 10px;font-size:1.15rem;}
    .brand-sub {font-size:.69rem;letter-spacing:.09em;color:#8c89a0;margin:5px 0 28px 42px;}
    .hero {background:linear-gradient(110deg,#292344 0%,#443578 65%,#6450a6 100%);color:white;border-radius:18px;padding:27px 30px;margin:18px 0 26px;}
    .hero h2 {color:white!important;font-size:1.55rem;margin:0 0 8px;}
    .hero p {color:#e1dbf4;font-size:.94rem;line-height:1.6;max-width:760px;margin:0;}
    .badge {display:inline-block;border:1px solid rgba(128,128,128,.22);border-radius:30px;padding:5px 11px;font-size:.70rem;margin-right:6px;}
    .status-dot {color:#16a994;}
    .note {border-left:3px solid #16a994;border-radius:0 10px 10px 0;background:rgba(22,169,148,.07);padding:16px 19px;line-height:1.65;font-size:.9rem;margin:18px 0;}
    .section-label {font-size:.72rem;font-weight:700;letter-spacing:.1em;color:#8c89a0;margin-top:10px;}
    .stButton button, .stDownloadButton button {border-radius:9px;font-weight:600;}
    [data-testid='stSidebar'] [role='radiogroup'] {gap:8px;}
    [data-testid='stSidebar'] [data-testid='stRadio'] label {font-size:.87rem;}
    @media(max-width:900px){.block-container{padding:4rem 1rem 1.5rem;} h1{font-size:1.9rem!important;}}
    @media(min-width:640px) and (max-width:900px){[data-testid='stHorizontalBlock']{flex-wrap:wrap;} [data-testid='stColumn']{min-width:46%!important;flex:1 1 46%!important;}}
    </style>""",
        unsafe_allow_html=True,
    )


def header(title, subtitle, section):
    st.markdown(f'<div class="eyebrow">Workspace / {section}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def chart(fig: go.Figure, title=None, height=360):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="DM Sans, Arial", size=12, color="#83889b"),
        title=title,
        margin=dict(l=15, r=20, t=40 if title else 15, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLORS,
        legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
    )
    fig.update_xaxes(gridcolor="rgba(128,128,128,.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,.12)", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def kpis(items):
    for col, (label, value, caption) in zip(st.columns(len(items)), items, strict=True):
        with col:
            st.metric(label, value)
            st.caption(caption)


def money(value):
    return f"−${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"
