import re
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Copa do Mundo · Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

    html, body, .stApp { font-family: 'DM Sans', system-ui, sans-serif; }

    /* ── Background ── */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse 120% 60% at 50% -10%, #0f1e30 0%, #06090f 55%);
        min-height: 100vh;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(175deg, #0b1020 0%, #060910 100%);
        border-right: 1px solid rgba(251,191,36,.1);
    }

    .sidebar-brand {
        text-align: center;
        padding: 1.2rem 0 .4rem;
    }
    .brand-icon {
        font-size: 2.6rem;
        line-height: 1;
        margin-bottom: .35rem;
        filter: drop-shadow(0 0 14px rgba(251,191,36,.55));
    }
    .brand-name {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.45rem;
        letter-spacing: .12em;
        color: #f1f5f9;
        line-height: 1;
    }
    .brand-tagline {
        color: #fbbf24;
        font-size: .64rem;
        font-weight: 600;
        letter-spacing: .22em;
        text-transform: uppercase;
        margin-top: .3rem;
    }

    /* ── Page header ── */
    .page-header { padding: 0 0 .5rem; }
    .header-eyebrow {
        color: #fbbf24;
        font-size: .72rem;
        font-weight: 600;
        letter-spacing: .22em;
        text-transform: uppercase;
        margin-bottom: .3rem;
    }
    .header-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.6rem;
        color: #f1f5f9;
        line-height: 1;
        letter-spacing: .06em;
        margin: 0;
    }
    .header-meta {
        color: #4e6070;
        font-size: .82rem;
        font-weight: 400;
        margin-top: .5rem;
        letter-spacing: .01em;
    }
    .header-meta strong { color: #94a3b8; font-weight: 500; }

    /* ── KPI cards ── */
    .kpi-card {
        background: rgba(255,255,255,.025);
        border: 1px solid rgba(251,191,36,.18);
        border-top: 3px solid #fbbf24;
        border-radius: 12px;
        padding: 22px 12px 16px;
        text-align: center;
        transition: border-color .25s, box-shadow .25s;
    }
    .kpi-card:hover {
        border-color: rgba(251,191,36,.38);
        border-top-color: #fbbf24;
        box-shadow: 0 0 24px rgba(251,191,36,.08);
    }
    .kpi-label {
        color: #4e6070;
        font-size: .65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .14em;
        margin-bottom: 10px;
    }
    .kpi-value {
        color: #fbbf24;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.3rem;
        line-height: 1;
        letter-spacing: .03em;
    }
    .kpi-sub {
        color: #334155;
        font-size: .65rem;
        margin-top: 7px;
        font-weight: 400;
        letter-spacing: .02em;
    }

    /* ── Tabs ── */
    div[data-testid="stTabs"] button {
        font-family: 'DM Sans', sans-serif;
        font-size: .875rem;
        font-weight: 500;
        letter-spacing: .02em;
    }

    /* ── Subheadings ── */
    h3 {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.35rem !important;
        letter-spacing: .08em !important;
        color: #cbd5e1 !important;
        font-weight: 400 !important;
        margin-bottom: .1rem !important;
    }

    /* ── Dividers ── */
    hr { border-color: rgba(251,191,36,.1) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constantes de tema ────────────────────────────────────────────────────────
T       = "plotly_dark"
GOLD    = "#fbbf24"
GREEN   = "#10b981"
RED     = "#ef4444"
CSCALE  = [[0.0, "#0c3d28"], [0.5, "#10b981"], [1.0, "#fbbf24"]]

# ── Helpers ───────────────────────────────────────────────────────────────────
def _simplify_stage(stage: str) -> str:
    s = str(stage).strip()
    if re.search(r"third|3rd place", s, re.I):
        return "3º Lugar"
    if re.search(r"^final$", s, re.I):
        return "Final"
    if re.search(r"semi", s, re.I):
        return "Semifinal"
    if re.search(r"quarter", s, re.I):
        return "Quartas"
    if re.search(r"round of 16|oitav", s, re.I):
        return "Oitavas"
    return "Fase de Grupos"


def _count_goals(event) -> int:
    if pd.isna(event):
        return 0
    s = str(event)
    total = len(re.findall(r"G\d+", s))
    own   = len(re.findall(r"OG\d+", s))
    return max(0, total - own)


# ── Carregamento dos dados ────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))

    cups = pd.read_csv(os.path.join(base, "WorldCups.csv"))
    cups["Attendance"] = (
        cups["Attendance"].astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    cups["Attendance"] = pd.to_numeric(cups["Attendance"], errors="coerce")

    matches = pd.read_csv(os.path.join(base, "WorldCupMatches.csv"))
    matches = matches.dropna(subset=["Home Team Name", "Away Team Name", "Year"])
    for col in ["Home Team Goals", "Away Team Goals"]:
        matches[col] = pd.to_numeric(matches[col], errors="coerce")
    matches = matches.dropna(subset=["Home Team Goals", "Away Team Goals"])
    matches["Year"] = matches["Year"].astype(int)
    matches["TotalGoals"] = matches["Home Team Goals"] + matches["Away Team Goals"]
    matches["Result"] = matches.apply(
        lambda r: "Mandante"
        if r["Home Team Goals"] > r["Away Team Goals"]
        else ("Visitante" if r["Home Team Goals"] < r["Away Team Goals"] else "Empate"),
        axis=1,
    )
    matches["Stage_simple"] = matches["Stage"].apply(_simplify_stage)

    players = pd.read_csv(os.path.join(base, "WorldCupPlayers.csv"))
    players = players.dropna(subset=["Player Name"])
    players["Goals"] = players["Event"].apply(_count_goals)

    return cups, matches, players


cups, matches, players = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-icon">⚽</div>
            <div class="brand-name">Copa do Mundo</div>
            <div class="brand-tagline">Dashboard FIFA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    years     = sorted(cups["Year"].unique())
    y_min, y_max = int(min(years)), int(max(years))
    sel_years = st.slider("Período", y_min, y_max, (y_min, y_max), step=4)

    all_teams = sorted(
        set(matches["Home Team Name"].dropna())
        | set(matches["Away Team Name"].dropna())
    )
    sel_team = st.selectbox("Seleção em destaque", ["— Todas —"] + all_teams)

    st.divider()
    st.caption("Fonte: FIFA World Cup Dataset")

# ── Filtros ───────────────────────────────────────────────────────────────────
cups_f    = cups[cups["Year"].between(*sel_years)]
matches_f = matches[matches["Year"].between(*sel_years)]
players_f = players[players["MatchID"].isin(matches_f["MatchID"])]

# ── Título ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="page-header">
        <div class="header-eyebrow">FIFA · História do Futebol Mundial</div>
        <h1 class="header-title">Copa do Mundo</h1>
        <div class="header-meta">
            Período: <strong>{sel_years[0]} – {sel_years[1]}</strong>
            &nbsp;·&nbsp; <strong>{len(cups_f)}</strong> edições
            &nbsp;·&nbsp; <strong>{len(matches_f):,}</strong> partidas
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
wc         = cups_f["Winner"].value_counts()
top_champ  = f"{wc.index[0]} ({int(wc.iloc[0])}×)" if len(wc) else "—"
gpm        = matches_f["TotalGoals"].mean() if len(matches_f) else 0
best_row   = cups_f.loc[cups_f["Attendance"].idxmax()] if not cups_f.empty else None
total_att  = int(cups_f["Attendance"].sum()) if not cups_f.empty else 0


def kpi(col, label, value, sub=""):
    col.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


k = st.columns(6)
kpi(k[0], "Edições",       len(cups_f),                               f"{sel_years[0]} – {sel_years[1]}")
kpi(k[1], "Partidas",      f"{len(matches_f):,}",                     "jogos disputados")
kpi(k[2], "Gols Totais",   f"{int(cups_f['GoalsScored'].sum()):,}",   f"média {cups_f['GoalsScored'].mean():.1f} / Copa")
kpi(k[3], "Gols / Jogo",   f"{gpm:.2f}",                              "média por partida")
kpi(k[4], "Maior Campeão", top_champ,                                  "no período")
if best_row is not None:
    kpi(k[5], "Maior Público",
        f"{int(best_row['Attendance']):,}",
        f"{best_row['Country']} · {int(best_row['Year'])}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Abas ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Edições & Tendências",
    "⚽ Análise de Partidas",
    "🌍 Seleções",
    "🥇 Artilheiros",
])

_layout = dict(
    template=T,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, system-ui", color="#94a3b8"),
    xaxis_gridcolor="rgba(255,255,255,.05)",
    xaxis_linecolor="rgba(255,255,255,.08)",
    yaxis_gridcolor="rgba(255,255,255,.05)",
    yaxis_linecolor="rgba(255,255,255,.08)",
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Edições
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Gols por Edição")
        avg_g = cups_f["GoalsScored"].mean()
        fig = go.Figure()
        fig.add_bar(
            x=cups_f["Year"], y=cups_f["GoalsScored"],
            name="Gols", marker_color=GREEN,
            marker_line_width=0,
            text=cups_f["GoalsScored"], textposition="outside",
            hovertemplate="<b>%{x}</b><br>Gols: %{y}<extra></extra>",
        )
        fig.add_scatter(
            x=cups_f["Year"], y=[avg_g] * len(cups_f),
            mode="lines", name=f"Média ({avg_g:.0f})",
            line=dict(color=GOLD, dash="dash", width=2),
        )
        fig.update_layout(
            **_layout, height=370,
            xaxis=dict(tickvals=cups_f["Year"].tolist(), tickangle=-45,
                       gridcolor="rgba(255,255,255,.05)"),
            yaxis_title="Gols", xaxis_title="Edição",
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Público Total por Edição")
        fig = go.Figure()
        fig.add_scatter(
            x=cups_f["Year"], y=cups_f["Attendance"],
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(16,185,129,.12)",
            line=dict(color=GOLD, width=2.5),
            marker=dict(color=GOLD, size=9, line=dict(color="#06090f", width=2)),
            customdata=cups_f[["Country"]].values,
            hovertemplate="<b>%{x}</b> · %{customdata[0]}<br>Público: %{y:,}<extra></extra>",
        )
        fig.update_layout(
            **_layout, height=370,
            xaxis=dict(tickvals=cups_f["Year"].tolist(), tickangle=-45,
                       gridcolor="rgba(255,255,255,.05)"),
            yaxis_title="Espectadores", xaxis_title="Edição",
        )
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Títulos por Seleção")
        champ = cups_f["Winner"].value_counts().reset_index()
        champ.columns = ["Seleção", "Títulos"]
        fig = px.bar(
            champ, x="Títulos", y="Seleção", orientation="h",
            height=370,
            color="Títulos", color_continuous_scale=CSCALE,
            text="Títulos",
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Evolução: Equipes & Partidas por Edição")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=cups_f["Year"], y=cups_f["QualifiedTeams"],
                mode="lines+markers", name="Equipes",
                marker=dict(color=GOLD, size=8, line=dict(color="#06090f", width=2)),
                line=dict(color=GOLD, width=2.5),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Bar(
                x=cups_f["Year"], y=cups_f["MatchesPlayed"],
                name="Partidas", marker_color=GREEN, opacity=0.6,
                marker_line_width=0,
            ),
            secondary_y=True,
        )
        fig.update_layout(
            **_layout, height=370,
            xaxis=dict(tickvals=cups_f["Year"].tolist(), tickangle=-45,
                       gridcolor="rgba(255,255,255,.05)"),
            legend=dict(orientation="h", y=1.08),
            barmode="overlay",
        )
        fig.update_yaxes(title_text="Equipes",  secondary_y=False,
                         gridcolor="rgba(255,255,255,.05)")
        fig.update_yaxes(title_text="Partidas", secondary_y=True,
                         gridcolor="rgba(255,255,255,.05)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Histórico de Pódios")
    podium_cols = ["Year", "Country", "Winner", "Runners-Up", "Third", "Fourth",
                   "GoalsScored", "MatchesPlayed", "Attendance"]
    st.dataframe(
        cups_f[podium_cols].sort_values("Year", ascending=False)
        .rename(columns={
            "Year": "Ano", "Country": "Sede", "Winner": "Campeão",
            "Runners-Up": "Vice", "Third": "3º Lugar", "Fourth": "4º Lugar",
            "GoalsScored": "Gols", "MatchesPlayed": "Partidas",
            "Attendance": "Público",
        })
        .reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Partidas
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Distribuição de Resultados")
        res = matches_f["Result"].value_counts().reset_index()
        res.columns = ["Resultado", "Qtd"]
        fig = go.Figure(go.Pie(
            labels=res["Resultado"], values=res["Qtd"],
            hole=0.52,
            marker=dict(
                colors=[GREEN, GOLD, "#334155"],
                line=dict(color="#06090f", width=3),
            ),
            textinfo="percent+label",
            pull=[0.04, 0.04, 0.02],
            hovertemplate="<b>%{label}</b><br>%{value:,} jogos (%{percent})<extra></extra>",
        ))
        fig.update_layout(
            **_layout, height=370,
            annotations=[dict(
                text=f"<b>{len(matches_f):,}</b><br><span style='font-size:11px'>jogos</span>",
                x=0.5, y=0.5, font_size=16, showarrow=False,
                font_color=GOLD,
            )],
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Gols por Fase")
        stage_order = ["Fase de Grupos", "Oitavas", "Quartas", "Semifinal", "3º Lugar", "Final"]
        sg = (
            matches_f.groupby("Stage_simple")["TotalGoals"]
            .agg(Total="sum", Media="mean", Partidas="count")
            .reset_index()
            .rename(columns={"Stage_simple": "Fase"})
        )
        sg["Fase"] = pd.Categorical(sg["Fase"], categories=stage_order, ordered=True)
        sg = sg.sort_values("Fase")
        fig = px.bar(
            sg, x="Fase", y="Total",
            height=370,
            color="Media", color_continuous_scale=CSCALE,
            text=sg["Total"],
            hover_data={"Partidas": True, "Media": ":.2f"},
            labels={"Total": "Gols Totais", "Media": "Média/Jogo"},
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(
            **_layout,
            coloraxis_colorbar=dict(title="Média/Jogo"),
        )
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Média de Gols por Jogo · por Edição")
        gpy = matches_f.groupby("Year")["TotalGoals"].mean().reset_index()
        gpy.columns = ["Ano", "Média"]
        overall = gpy["Média"].mean()
        fig = px.line(
            gpy, x="Ano", y="Média",
            height=370,
            markers=True, color_discrete_sequence=[GOLD],
            labels={"Ano": "Edição", "Média": "Gols/Jogo"},
        )
        fig.update_traces(
            marker=dict(size=9, line=dict(color="#06090f", width=2)),
            line=dict(width=2.5),
        )
        fig.add_hline(
            y=overall, line_dash="dash", line_color=GREEN,
            annotation_text=f"Média geral: {overall:.2f}",
            annotation_position="bottom right",
            annotation_font_color=GREEN,
        )
        fig.update_xaxes(tickvals=gpy["Ano"].tolist(), tickangle=-45)
        fig.update_layout(**_layout)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Top 10 Estádios por Número de Partidas")
        stad = (
            matches_f.groupby("Stadium")
            .agg(Partidas=("MatchID", "count"), Gols=("TotalGoals", "sum"))
            .sort_values("Partidas", ascending=False)
            .head(10)
            .reset_index()
        )
        fig = px.bar(
            stad, x="Partidas", y="Stadium", orientation="h",
            height=370,
            color="Gols", color_continuous_scale=CSCALE,
            text="Partidas",
            labels={"Stadium": "Estádio", "Gols": "Gols"},
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gols Mandante vs. Visitante por Edição")
    ghv = matches_f.groupby("Year").agg(
        Mandante=("Home Team Goals", "sum"),
        Visitante=("Away Team Goals", "sum"),
    ).reset_index()
    fig = go.Figure()
    fig.add_bar(x=ghv["Year"], y=ghv["Mandante"], name="Mandante",
                marker_color=GREEN, marker_line_width=0,
                text=ghv["Mandante"], textposition="inside")
    fig.add_bar(x=ghv["Year"], y=ghv["Visitante"], name="Visitante",
                marker_color=GOLD, marker_line_width=0,
                text=ghv["Visitante"], textposition="inside")
    fig.update_layout(
        **_layout, barmode="stack", height=360,
        xaxis=dict(tickvals=ghv["Year"].tolist(), tickangle=-45,
                   gridcolor="rgba(255,255,255,.05)"),
        yaxis_title="Gols", xaxis_title="Edição",
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Seleções
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    home_df = matches_f[["Home Team Name", "Home Team Goals", "Away Team Goals"]].copy()
    home_df.columns = ["Team", "GF", "GA"]
    away_df = matches_f[["Away Team Name", "Away Team Goals", "Home Team Goals"]].copy()
    away_df.columns = ["Team", "GF", "GA"]
    all_m = pd.concat([home_df, away_df], ignore_index=True)
    all_m["W"] = (all_m["GF"] > all_m["GA"]).astype(int)
    all_m["D"] = (all_m["GF"] == all_m["GA"]).astype(int)
    all_m["L"] = (all_m["GF"] < all_m["GA"]).astype(int)

    ts = (
        all_m.groupby("Team")
        .agg(Jogos=("GF", "count"), GF=("GF", "sum"), GA=("GA", "sum"),
             V=("W", "sum"), E=("D", "sum"), D=("L", "sum"))
        .reset_index()
    )
    ts["Saldo"] = ts["GF"] - ts["GA"]
    ts["Aproveitamento"] = ((ts["V"] * 3 + ts["E"]) / (ts["Jogos"] * 3) * 100).round(1)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top 15 — Gols Marcados")
        top_gf = ts.sort_values("GF", ascending=False).head(15)
        fig = px.bar(
            top_gf, x="GF", y="Team", orientation="h",
            height=420,
            color="GF", color_continuous_scale=CSCALE,
            text="GF", labels={"GF": "Gols", "Team": "Seleção"},
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Top 15 — Vitórias")
        top_w = ts.sort_values("V", ascending=False).head(15)
        fig = px.bar(
            top_w, x="V", y="Team", orientation="h",
            height=420,
            color="V", color_continuous_scale=CSCALE,
            text="V", labels={"V": "Vitórias", "Team": "Seleção"},
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    if sel_team != "— Todas —":
        st.divider()
        st.subheader(f"Histórico: {sel_team}")
        tm = matches_f[
            (matches_f["Home Team Name"] == sel_team) |
            (matches_f["Away Team Name"] == sel_team)
        ].copy()
        tm["TGols"]  = tm.apply(lambda r: r["Home Team Goals"] if r["Home Team Name"] == sel_team else r["Away Team Goals"], axis=1)
        tm["OGols"]  = tm.apply(lambda r: r["Away Team Goals"] if r["Home Team Name"] == sel_team else r["Home Team Goals"], axis=1)
        tm["ResTeam"] = tm.apply(
            lambda r: "Vitória" if r["TGols"] > r["OGols"]
            else ("Derrota" if r["TGols"] < r["OGols"] else "Empate"),
            axis=1,
        )

        dx, dy = st.columns(2)
        with dx:
            perf = tm.groupby("Year")[["TGols", "OGols"]].sum().reset_index()
            fig = go.Figure()
            fig.add_bar(x=perf["Year"], y=perf["TGols"], name="Marcados",
                        marker_color=GREEN, marker_line_width=0)
            fig.add_bar(x=perf["Year"], y=perf["OGols"], name="Sofridos",
                        marker_color=RED, marker_line_width=0)
            fig.update_layout(
                **_layout, barmode="group", height=320,
                xaxis=dict(tickvals=perf["Year"].tolist(), tickangle=-45,
                           gridcolor="rgba(255,255,255,.05)"),
                yaxis_title="Gols",
                legend=dict(orientation="h", y=1.08),
            )
            st.plotly_chart(fig, use_container_width=True)

        with dy:
            res_t = tm["ResTeam"].value_counts().reset_index()
            res_t.columns = ["Resultado", "Qtd"]
            fig = px.pie(
                res_t, names="Resultado", values="Qtd",
                height=320, hole=0.48,
                color_discrete_sequence=[GREEN, RED, GOLD],
                title=f"Resultados · {sel_team}",
            )
            fig.update_traces(
                textinfo="percent+label",
                marker=dict(line=dict(color="#06090f", width=3)),
            )
            fig.update_layout(**_layout)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Ranking Geral por Seleção (Top 30)")
    display = (
        ts.sort_values("GF", ascending=False)
        .head(30)
        .rename(columns={
            "Team": "Seleção", "Jogos": "Jogos", "GF": "Gols Pró",
            "GA": "Gols Contra", "V": "Vitórias", "E": "Empates",
            "D": "Derrotas", "Saldo": "Saldo", "Aproveitamento": "Aprov. (%)",
        })
        .reset_index(drop=True)
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Artilheiros
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    top_scorers = (
        players_f[players_f["Goals"] > 0]
        .groupby(["Player Name", "Team Initials"])["Goals"]
        .sum()
        .reset_index()
        .sort_values("Goals", ascending=False)
        .head(20)
        .rename(columns={"Player Name": "Jogador", "Team Initials": "Seleção", "Goals": "Gols"})
    )

    c1, c2 = st.columns([3, 2])

    with c1:
        st.subheader("Top 20 Artilheiros Históricos")
        fig = px.bar(
            top_scorers, x="Gols", y="Jogador", orientation="h",
            height=580,
            color="Gols", color_continuous_scale=CSCALE,
            text="Gols",
            hover_data={"Seleção": True},
            labels={"Gols": "Gols", "Jogador": "Jogador"},
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Top 12 Seleções por Gols (jogadores)")
        team_goals = (
            players_f.groupby("Team Initials")["Goals"]
            .sum()
            .reset_index()
            .sort_values("Goals", ascending=False)
            .head(12)
            .rename(columns={"Team Initials": "Seleção", "Goals": "Gols"})
        )
        fig = px.bar(
            team_goals, x="Gols", y="Seleção", orientation="h",
            height=360,
            color="Gols", color_continuous_scale=CSCALE,
            text="Gols",
        )
        fig.update_layout(
            **_layout,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Gols por Posição")
        pos = (
            players_f[players_f["Position"].notna() & (players_f["Position"].str.strip() != "")]
            .groupby("Position")["Goals"]
            .sum()
            .reset_index()
            .sort_values("Goals", ascending=False)
            .rename(columns={"Position": "Posição", "Goals": "Gols"})
        )
        fig = px.pie(
            pos, names="Posição", values="Gols",
            height=220, hole=0.46,
            color_discrete_sequence=[GOLD, GREEN, "#475569", RED, "#38bdf8", "#a78bfa"],
        )
        fig.update_traces(
            textinfo="percent+label",
            marker=dict(line=dict(color="#06090f", width=3)),
        )
        fig.update_layout(
            **_layout,
            showlegend=False,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Tabela de Artilheiros (Top 50)")
    full_scorers = (
        players_f[players_f["Goals"] > 0]
        .groupby(["Player Name", "Team Initials"])["Goals"]
        .sum()
        .reset_index()
        .sort_values("Goals", ascending=False)
        .head(50)
        .rename(columns={"Player Name": "Jogador", "Team Initials": "Seleção", "Goals": "Gols"})
        .reset_index(drop=True)
    )
    full_scorers.index += 1
    st.dataframe(full_scorers, use_container_width=True)
