"""
PropLens India — Dashboard Styles & Theme System
=================================================
Luxury minimal aesthetic inspired by high-end real estate brands.
Dark backgrounds, editorial typography, muted gold accents.

Import this module at the top of every tab file:
    from styles import *
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_primary": "#0D0D0D",
    "bg_secondary": "#1A1A1A",
    "bg_tertiary": "#111111",
    "bg_card": "#1A1A1A",
    "bg_card_hover": "#222222",
    "bg_table_alt": "#161616",

    # Accent
    "accent_gold": "#C9A96E",
    "accent_gold_dim": "#A08550",
    "accent_gold_glow": "rgba(201, 169, 110, 0.15)",

    # Text
    "text_primary": "#F5F0EB",
    "text_secondary": "#8A8480",
    "text_muted": "#5A5550",

    # Chart colours
    "chart_positive": "#C9A96E",
    "chart_neutral": "#4A5568",
    "chart_negative": "#A0616A",
    "chart_accent2": "#6B8E7B",
    "chart_accent3": "#8B7355",
    "chart_accent4": "#7B8FA0",
    "chart_accent5": "#9B8EA0",

    # Grid / Dividers
    "grid_line": "#2A2A2A",
    "divider": "#2A2A2A",
    "border_gold": "rgba(201, 169, 110, 0.3)",

    # Status
    "positive": "#6B8E7B",
    "negative": "#A0616A",
    "warning": "#D4A843",
}

# Plotly colour sequence
CHART_COLORWAY = [
    COLORS["chart_positive"],
    COLORS["chart_neutral"],
    COLORS["chart_negative"],
    COLORS["chart_accent2"],
    COLORS["chart_accent3"],
    COLORS["chart_accent4"],
    COLORS["chart_accent5"],
]

# ─────────────────────────────────────────────
# TYPOGRAPHY
# ─────────────────────────────────────────────

FONTS = {
    "heading": "'Playfair Display', Georgia, serif",
    "body": "'Inter', 'DM Sans', -apple-system, sans-serif",
    "mono": "'DM Mono', 'JetBrains Mono', 'Fira Code', monospace",
}

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:wght@400;500;600;700&"
    "family=Inter:wght@300;400;500;600&"
    "family=DM+Sans:wght@400;500;600&"
    "family=DM+Mono:wght@400;500&"
    "display=swap"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — INJECTED VIA st.markdown
# ─────────────────────────────────────────────

CUSTOM_CSS = f"""
<style>
    /* ── Google Fonts Import ── */
    @import url('{GOOGLE_FONTS_URL}');

    /* ── Global Background Override ── */
    .stApp {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
    }}

    /* ── Main Content Area ── */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['bg_secondary']} !important;
        border-right: 1px solid {COLORS['border_gold']};
    }}

    [data-testid="stSidebar"] .stMarkdown {{
        color: {COLORS['text_secondary']};
    }}

    /* Sidebar active radio highlight */
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {{
        color: {COLORS['accent_gold']} !important;
        font-weight: 500;
    }}

    /* ── Typography ── */
    h1, h2, h3 {{
        font-family: {FONTS['heading']} !important;
        color: {COLORS['text_primary']} !important;
        letter-spacing: 0.02em;
    }}

    h1 {{
        font-size: 2.4rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }}

    h2 {{
        font-size: 1.6rem !important;
        font-weight: 500 !important;
    }}

    h3 {{
        font-size: 1.2rem !important;
        font-weight: 500 !important;
    }}

    p, span, label, .stMarkdown {{
        font-family: {FONTS['body']} !important;
    }}

    /* ── Category Labels / Tags ── */
    .category-label {{
        font-family: {FONTS['body']};
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: {COLORS['text_secondary']};
    }}

    /* ── Metric Cards ── */
    [data-testid="stMetric"] {{
        background-color: {COLORS['bg_card']};
        border-top: 2px solid {COLORS['accent_gold']};
        border-radius: 4px;
        padding: 1.2rem 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}

    [data-testid="stMetric"] label {{
        font-family: {FONTS['heading']} !important;
        color: {COLORS['text_secondary']} !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.04em;
    }}

    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-family: {FONTS['mono']} !important;
        color: {COLORS['text_primary']} !important;
        font-size: 1.8rem !important;
        font-weight: 500 !important;
    }}

    [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        font-family: {FONTS['mono']} !important;
        font-size: 0.75rem !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: {COLORS['bg_secondary']};
        border-radius: 4px;
        padding: 4px;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-family: {FONTS['body']} !important;
        font-size: 0.8rem !important;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {COLORS['text_secondary']} !important;
        background-color: transparent;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 3px;
        transition: all 0.2s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLORS['text_primary']} !important;
        background-color: {COLORS['bg_tertiary']};
    }}

    .stTabs [aria-selected="true"] {{
        color: {COLORS['accent_gold']} !important;
        background-color: {COLORS['bg_tertiary']} !important;
        border-bottom: 2px solid {COLORS['accent_gold']} !important;
    }}

    /* Remove default tab underline */
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}

    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        font-family: {FONTS['body']} !important;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.75rem;
        background-color: transparent !important;
        color: {COLORS['accent_gold']} !important;
        border: 1px solid {COLORS['accent_gold']} !important;
        border-radius: 3px;
        padding: 0.5rem 1.5rem;
        transition: all 0.25s ease;
    }}

    .stButton > button:hover {{
        background-color: {COLORS['accent_gold_glow']} !important;
        box-shadow: 0 0 12px {COLORS['accent_gold_glow']};
    }}

    .stDownloadButton > button {{
        font-family: {FONTS['body']} !important;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.75rem;
        background-color: {COLORS['accent_gold']} !important;
        color: {COLORS['bg_primary']} !important;
        border: none !important;
        border-radius: 3px;
        padding: 0.5rem 1.5rem;
    }}

    /* ── Selectbox / Dropdowns ── */
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label {{
        font-family: {FONTS['body']} !important;
        color: {COLORS['text_secondary']} !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}

    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stMultiSelect"] [data-baseweb="select"] {{
        background-color: {COLORS['bg_secondary']} !important;
        border-color: {COLORS['grid_line']} !important;
    }}

    /* ── Sliders ── */
    [data-testid="stSlider"] label {{
        font-family: {FONTS['body']} !important;
        color: {COLORS['text_secondary']} !important;
        font-size: 0.8rem !important;
    }}

    .stSlider [data-baseweb="slider"] [role="slider"] {{
        background-color: {COLORS['accent_gold']} !important;
    }}

    /* ── Number Inputs ── */
    [data-testid="stNumberInput"] label {{
        font-family: {FONTS['body']} !important;
        color: {COLORS['text_secondary']} !important;
        font-size: 0.8rem !important;
    }}

    [data-testid="stNumberInput"] input {{
        background-color: {COLORS['bg_secondary']} !important;
        color: {COLORS['text_primary']} !important;
        border-color: {COLORS['grid_line']} !important;
        font-family: {FONTS['mono']} !important;
    }}

    /* ── Data Tables ── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {COLORS['border_gold']};
        border-radius: 4px;
        overflow: hidden;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        font-family: {FONTS['heading']} !important;
        color: {COLORS['text_primary']} !important;
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['grid_line']};
    }}

    /* ── Divider ── */
    hr {{
        border: none;
        height: 1px;
        background-color: {COLORS['accent_gold']};
        opacity: 0.3;
        margin: 2rem 0;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: {COLORS['bg_primary']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {COLORS['grid_line']};
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['accent_gold_dim']};
    }}

    /* ── Custom Components ── */
    .hero-banner {{
        background: linear-gradient(135deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_primary']} 100%);
        padding: 2.5rem 2rem 2rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-bottom: 1px solid {COLORS['accent_gold']};
    }}

    .hero-title {{
        font-family: {FONTS['heading']};
        font-size: 2.4rem;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
    }}

    .hero-subtitle {{
        font-family: {FONTS['body']};
        font-size: 0.95rem;
        color: {COLORS['text_secondary']};
        margin: 0 0 1rem 0;
        font-weight: 300;
        letter-spacing: 0.02em;
    }}

    .hero-line {{
        width: 60px;
        height: 2px;
        background-color: {COLORS['accent_gold']};
        margin-top: 0.5rem;
    }}

    .metric-card {{
        background-color: {COLORS['bg_card']};
        border-top: 2px solid {COLORS['accent_gold']};
        border-radius: 4px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }}

    .metric-label {{
        font-family: {FONTS['heading']};
        font-size: 0.85rem;
        color: {COLORS['text_secondary']};
        letter-spacing: 0.04em;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-family: {FONTS['mono']};
        font-size: 1.8rem;
        font-weight: 500;
        color: {COLORS['text_primary']};
        line-height: 1.2;
    }}

    .metric-delta {{
        font-family: {FONTS['mono']};
        font-size: 0.75rem;
        margin-top: 0.3rem;
    }}

    .metric-delta.positive {{
        color: {COLORS['positive']};
    }}

    .metric-delta.negative {{
        color: {COLORS['negative']};
    }}

    .gold-divider {{
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            {COLORS['accent_gold']} 20%,
            {COLORS['accent_gold']} 80%,
            transparent 100%
        );
        opacity: 0.4;
        margin: 2rem 0;
    }}

    .verdict-card {{
        background: linear-gradient(135deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_tertiary']} 100%);
        border: 1px solid {COLORS['accent_gold']};
        border-radius: 6px;
        padding: 1.5rem 2rem;
        text-align: center;
    }}

    .verdict-title {{
        font-family: {FONTS['heading']};
        font-size: 1.2rem;
        color: {COLORS['accent_gold']};
        margin-bottom: 0.5rem;
    }}

    .verdict-text {{
        font-family: {FONTS['body']};
        font-size: 0.95rem;
        color: {COLORS['text_primary']};
    }}

    .sidebar-brand {{
        font-family: {FONTS['heading']};
        font-size: 1.6rem;
        font-weight: 600;
        color: {COLORS['text_primary']};
        letter-spacing: 0.05em;
        padding: 1rem 0;
        border-bottom: 1px solid {COLORS['border_gold']};
        margin-bottom: 1.5rem;
    }}

    .sidebar-brand span {{
        color: {COLORS['accent_gold']};
    }}

    .data-freshness {{
        font-family: {FONTS['mono']};
        font-size: 0.7rem;
        color: {COLORS['text_muted']};
        padding: 1rem 0;
        border-top: 1px solid {COLORS['grid_line']};
        margin-top: 2rem;
    }}

    .data-freshness .dot {{
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: {COLORS['accent_gold']};
        margin-right: 6px;
        animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.4; }}
    }}

    .comparison-better {{
        background-color: rgba(107, 142, 123, 0.15);
        border-left: 3px solid {COLORS['positive']};
        padding: 0.5rem 1rem;
        border-radius: 0 4px 4px 0;
    }}

    .comparison-worse {{
        background-color: rgba(160, 97, 106, 0.1);
        padding: 0.5rem 1rem;
    }}

    /* ── Toggle / Radio as Mode Switcher ── */
    .mode-toggle {{
        display: flex;
        gap: 0;
        background-color: {COLORS['bg_secondary']};
        border-radius: 4px;
        padding: 3px;
        border: 1px solid {COLORS['grid_line']};
    }}

    /* ── Folium Map Container ── */
    .map-container {{
        border: 1px solid {COLORS['border_gold']};
        border-radius: 4px;
        overflow: hidden;
        margin: 1rem 0;
    }}

    /* ── Hide Streamlit Branding ── */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
</style>
"""


# ─────────────────────────────────────────────
# PLOTLY TEMPLATE
# ─────────────────────────────────────────────

def _build_plotly_template():
    """Build and register the PropLens Plotly template."""
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor=COLORS["bg_tertiary"],
        plot_bgcolor=COLORS["bg_tertiary"],
        font=dict(
            family=FONTS["body"],
            color=COLORS["text_primary"],
            size=12,
        ),
        title=dict(
            font=dict(
                family=FONTS["heading"],
                color=COLORS["text_primary"],
                size=18,
            ),
            x=0,
            xanchor="left",
            pad=dict(l=10, t=10),
        ),
        xaxis=dict(
            gridcolor=COLORS["grid_line"],
            linecolor=COLORS["grid_line"],
            zerolinecolor=COLORS["grid_line"],
            color=COLORS["text_secondary"],
            tickfont=dict(family=FONTS["body"], size=11),
            title_font=dict(family=FONTS["body"], size=12, color=COLORS["text_secondary"]),
        ),
        yaxis=dict(
            gridcolor=COLORS["grid_line"],
            linecolor=COLORS["grid_line"],
            zerolinecolor=COLORS["grid_line"],
            color=COLORS["text_secondary"],
            tickfont=dict(family=FONTS["body"], size=11),
            title_font=dict(family=FONTS["body"], size=12, color=COLORS["text_secondary"]),
        ),
        colorway=CHART_COLORWAY,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text_secondary"], size=11),
            bordercolor=COLORS["grid_line"],
            borderwidth=0,
        ),
        hoverlabel=dict(
            bgcolor=COLORS["bg_secondary"],
            bordercolor=COLORS["accent_gold"],
            font=dict(
                family=FONTS["body"],
                color=COLORS["text_primary"],
                size=12,
            ),
        ),
    )
    pio.templates["proplens"] = template
    pio.templates.default = "proplens"


# Build on import
_build_plotly_template()


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def inject_styles():
    """Inject all custom CSS into the Streamlit app. Call once at the top of app.py."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str):
    """Render a full-width hero banner for a tab."""
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
            <div class="hero-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, delta: str = None, delta_positive: bool = True):
    """Render a styled metric card with gold top border."""
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_positive else "negative"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_divider():
    """Render a thin gold horizontal divider."""
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)


def render_verdict(title: str, text: str):
    """Render a verdict/insight card with gold border."""
    st.markdown(
        f"""
        <div class="verdict-card">
            <div class="verdict-title">{title}</div>
            <div class="verdict-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_category_label(text: str):
    """Render an uppercase category label."""
    st.markdown(f'<div class="category-label">{text}</div>', unsafe_allow_html=True)


def render_sidebar_brand():
    """Render the PropLens brand in the sidebar."""
    st.sidebar.markdown(
        '<div class="sidebar-brand">Prop<span>Lens</span> India</div>',
        unsafe_allow_html=True,
    )


def render_data_freshness(date_str: str):
    """Render the data freshness indicator in the sidebar."""
    st.sidebar.markdown(
        f"""
        <div class="data-freshness">
            <span class="dot"></span>
            Data last updated: {date_str}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_plotly_layout(**overrides) -> dict:
    """Return a themed Plotly layout dict with optional overrides."""
    base = dict(
        paper_bgcolor=COLORS["bg_tertiary"],
        plot_bgcolor=COLORS["bg_tertiary"],
        font=dict(family=FONTS["body"], color=COLORS["text_primary"], size=12),
        title_font=dict(family=FONTS["heading"], color=COLORS["text_primary"]),
        xaxis=dict(gridcolor=COLORS["grid_line"], color=COLORS["text_secondary"]),
        yaxis=dict(gridcolor=COLORS["grid_line"], color=COLORS["text_secondary"]),
        margin=dict(l=40, r=20, t=60, b=40),
        hoverlabel=dict(
            bgcolor=COLORS["bg_secondary"],
            bordercolor=COLORS["accent_gold"],
            font_color=COLORS["text_primary"],
        ),
    )
    base.update(overrides)
    return base


def format_inr(value, compact: bool = True) -> str:
    """Format a number as Indian Rupees."""
    if value is None:
        return "—"
    if compact:
        if abs(value) >= 1e7:
            return f"₹{value / 1e7:.2f} Cr"
        elif abs(value) >= 1e5:
            return f"₹{value / 1e5:.2f} L"
        elif abs(value) >= 1e3:
            return f"₹{value / 1e3:.1f}K"
    return f"₹{value:,.0f}"


def format_pct(value) -> str:
    """Format a number as percentage."""
    if value is None:
        return "—"
    return f"{value:.2f}%"


def style_dataframe_for_display(df):
    """Apply luxury dark styling to a pandas DataFrame for st.dataframe."""
    return df.style.set_properties(**{
        'background-color': COLORS['bg_tertiary'],
        'color': COLORS['text_primary'],
        'border-color': COLORS['grid_line'],
        'font-family': FONTS['body'],
        'font-size': '0.85rem',
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', COLORS['bg_secondary']),
            ('color', COLORS['accent_gold']),
            ('font-family', FONTS['body']),
            ('font-weight', '600'),
            ('text-transform', 'uppercase'),
            ('letter-spacing', '0.06em'),
            ('font-size', '0.75rem'),
            ('border-bottom', f'1px solid {COLORS["accent_gold"]}'),
        ]},
        {'selector': 'td', 'props': [
            ('border-bottom', f'1px solid {COLORS["grid_line"]}'),
        ]},
        {'selector': 'tr:nth-of-type(even)', 'props': [
            ('background-color', COLORS['bg_table_alt']),
        ]},
    ])
