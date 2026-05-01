from dash import Dash, html, dcc, Input, Output, State, ctx, ALL
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("basketballadvanced2026_cleaned.csv")

app = Dash(__name__, suppress_callback_exceptions=True)

# -----------------------------
# CONSTANTS
# -----------------------------
GOLD = "#C9A84C"
GOLD_LIGHT = "#F0C96B"
BG = "#0A0E1A"
PANEL = "#10162A"
TEXT = "#E8E8E8"
GREY = "#5A6070"
WHITE = "#FFFFFF"
HIGHLIGHT_YELLOW = "#FFD700"
OTHER_CANDIDATE_RED = "#FF4C4C"

players = {
    "wemby": {
        "name": "Victor Wembanyama",
        "short": "WEMBY",
        "team": "San Antonio Spurs",
        "img": "https://cdn.nba.com/headshots/nba/latest/1040x760/1641705.png",
        "search": "Wembanyama",
        "color": "#00bcd4",
        "argument": "Wembanyama's defensive dominance combined with elite offense at his size makes him historically unprecedented."
    },
    "Jokic": {
        "name": "Nikola Jokic",
        "short": "JOKIĆ",
        "team": "Denver Nuggets",
        "img": "https://cdn.nba.com/headshots/nba/latest/1040x760/203999.png",
        "search": "Jokic",
        "color": "#FFC72C",
        "argument": "Jokic's VORP and PER lead all players — his all-around statistical dominance is unmatched in league history."
    },
    "shai": {
        "name": "Shai Gilgeous-Alexander",
        "short": "SGA",
        "team": "Oklahoma City Thunder",
        "img": "https://cdn.nba.com/headshots/nba/latest/1040x760/1628983.png",
        "search": "Gilgeous",
        "color": "#007AC1",
        "argument": "SGA's efficiency and win shares on the league's best team make him the most impactful player this season."
    }
}

PLAYER_KEYS = list(players.keys())

# -----------------------------
# CHART THEMES
# -----------------------------
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(16,22,42,0.9)",
    font=dict(family="Georgia, serif", color=TEXT, size=11),
    margin=dict(l=40, r=20, t=50, b=40),
    xaxis=dict(gridcolor="#1E2640", zerolinecolor="#1E2640", color=TEXT),
    yaxis=dict(gridcolor="#1E2640", zerolinecolor="#1E2640", color=TEXT),
)

def styled_scatter(df_all, x, y, highlight_df, color, title, x_label=None, y_label=None, other_rows=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_all[x], y=df_all[y],
        mode="markers",
        marker=dict(size=6, color=GREY, opacity=0.4),
        name="All Players",
        hovertemplate="%{text}<br>" + (x_label or x) + ": %{x}<br>" + (y_label or y) + ": %{y}<extra></extra>",
        text=df_all.get("Player", df_all.index).astype(str)
    ))
    if other_rows is not None and not other_rows.empty:
        fig.add_trace(go.Scatter(
            x=other_rows[x], y=other_rows[y],
            mode="markers",
            marker=dict(size=12, color=OTHER_CANDIDATE_RED, symbol="x", opacity=0.85),
            name="Other MVP Candidates",
            hovertemplate="%{text}<br>" + (x_label or x) + ": %{x}<br>" + (y_label or y) + ": %{y}<extra></extra>",
            text=other_rows.get("Player", other_rows.index).astype(str)
        ))
    if not highlight_df.empty:
        fig.add_trace(go.Scatter(
            x=highlight_df[x], y=highlight_df[y],
            mode="markers",
            marker=dict(size=18, color=HIGHLIGHT_YELLOW, symbol="diamond",
                        line=dict(color=WHITE, width=2)),
            name=highlight_df["Player"].values[0] if "Player" in highlight_df.columns else "Player",
            hovertemplate="%{text}<br>" + (x_label or x) + ": %{x}<br>" + (y_label or y) + ": %{y}<extra></extra>",
            text=highlight_df["Player"].astype(str)
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=GOLD), x=0.5),
        showlegend=False,
        **CHART_LAYOUT
    )
    return fig


def _find_column(columns):
    for col in columns:
        if col in df.columns:
            return col
    return None


def build_cohort_charts(row, x, y, x_label, y_label, color, player_short, other_rows):
    charts = []

    pos_col = _find_column(["Pos", "POSITION", "Position"])
    if pos_col is not None and not row.empty:
        pos = row[pos_col].values[0]
        cohort = df[df[pos_col] == pos]
        title = f"{x_label or x} vs {y_label or y} — {pos} Players"
        caption = f"{player_short} stands out among other {pos} players in the same metric set."
        charts.append((styled_scatter(cohort, x, y, row, color, title, x_label, y_label, other_rows=other_rows), caption))

    award_col = _find_column([
        "AllStar", "ALL_STAR", "All_Star", "All Star",
        "MVP", "MVPs", "MVP Award", "AllNBA", "All_NBA", "All-NBA", "Awards", "Award"
    ])
    if award_col is not None and not row.empty:
        award_mask = df[award_col].astype(str).str.contains(r"1|yes|true|MVP|All[-_ ]NBA|ALLNBA", case=False, na=False)
        cohort = df[award_mask]
        if len(cohort) > 0:
            title = f"{x_label or x} vs {y_label or y} — Award Winners"
            caption = f"{player_short} compared to the league's award-winning peers."
            charts.append((styled_scatter(cohort, x, y, row, color, title, x_label, y_label, other_rows=other_rows), caption))

    if len(charts) < 2:
        mp_col = _find_column(["MP", "Min", "MIN", "minutes", "Minutes"])
        if mp_col is not None and not row.empty:
            median_mp = df[mp_col].median()
            cohort = df[df[mp_col] >= median_mp]
            title = f"{x_label or x} vs {y_label or y} — High Minute Players"
            caption = f"{player_short} compared to players who get the most minutes."
            charts.append((styled_scatter(cohort, x, y, row, color, title, x_label, y_label, other_rows=other_rows), caption))

    if len(charts) < 2:
        threshold = df[y].quantile(0.75) if y in df.columns else None
        cohort = df[df[y] >= threshold] if threshold is not None else df
        title = f"{x_label or x} vs {y_label or y} — Top Cohort"
        caption = f"{player_short} compared to the top performers on this pair of metrics."
        charts.append((styled_scatter(cohort, x, y, row, color, title, x_label, y_label, other_rows=other_rows), caption))

    return charts[:2]


def get_player_row(name):
    return df[df["Player"].str.contains(name, case=False, na=False)]


def build_player_charts(player_key):
    p = players[player_key]
    row = get_player_row(p["search"])
    color = p["color"]
    other_candidate_rows = []
    for key in PLAYER_KEYS:
        if key == player_key:
            continue
        other_row = get_player_row(players[key]["search"])
        if not other_row.empty:
            other_candidate_rows.append(other_row)
    other_candidate_rows = pd.concat(other_candidate_rows, ignore_index=True) if other_candidate_rows else pd.DataFrame()

    if player_key == "Jokic":
        charts = [
            {
                "fig": styled_scatter(df, "AST%", "TRB%", row, color,
                    "Assist % vs Rebound %",
                    "Assist Rate (AST%)", "Rebound Rate (TRB%)", other_rows=other_candidate_rows),
                "caption": "No center in NBA history posts this AST%+TRB% combo.",
                "x": "AST%", "y": "TRB%",
                "x_label": "Assist Rate (AST%)", "y_label": "Rebound Rate (TRB%)"
            },
            {
                "fig": styled_scatter(df, "VORP", "PER", row, color,
                    "VORP vs Player Efficiency Rating",
                    "Value Over Replacement (VORP)", "Player Efficiency Rating (PER)", other_rows=other_candidate_rows),
                "caption": "Jokic leads the league in both VORP and PER — the two gold standards of player value.",
                "x": "VORP", "y": "PER",
                "x_label": "Value Over Replacement (VORP)", "y_label": "Player Efficiency Rating (PER)"
            },
            {
                "fig": styled_scatter(df, "VORP", "OWS", row, color,
                    "VORP vs Offensive Win Shares",
                    "Value Over Replacement (VORP)", "Offensive Win Shares (OWS)", other_rows=other_candidate_rows),
                "caption": "His offensive win shares relative to VORP show an outlier who wins games by himself.",
                "x": "VORP", "y": "OWS",
                "x_label": "Value Over Replacement (VORP)", "y_label": "Offensive Win Shares (OWS)"
            },
        ]
    elif player_key == "wemby":
        charts = [
            {
                "fig": styled_scatter(df, "PER", "VORP", row, color,
                    "Efficiency vs Overall Value",
                    "Player Efficiency Rating (PER)", "Value Over Replacement (VORP)", other_rows=other_candidate_rows),
                "caption": "Wemby's PER/VORP combo is extraordinary for a player his age in just his second season.",
                "x": "PER", "y": "VORP",
                "x_label": "Player Efficiency Rating (PER)", "y_label": "Value Over Replacement (VORP)"
            },
            {
                "fig": styled_scatter(df, "BLK%", "STL%", row, color,
                    "Block % vs Steal %",
                    "Block Rate (BLK%)", "Steal Rate (STL%)", other_rows=other_candidate_rows),
                "caption": "His defensive versatility — blocking shots AND stealing the ball — is historically rare.",
                "x": "BLK%", "y": "STL%",
                "x_label": "Block Rate (BLK%)", "y_label": "Steal Rate (STL%)"
            },
            {
                "fig": styled_scatter(df, "OWS", "DWS", row, color,
                    "Offensive vs Defensive Win Shares",
                    "Offensive Win Shares (OWS)", "Defensive Win Shares (DWS)", other_rows=other_candidate_rows),
                "caption": "Wemby contributes elite win shares on BOTH ends — virtually no one else does this.",
                "x": "OWS", "y": "DWS",
                "x_label": "Offensive Win Shares (OWS)", "y_label": "Defensive Win Shares (DWS)"
            },
        ]
    else:  # shai
        charts = [
            {
                "fig": styled_scatter(df, "PER", "VORP", row, color,
                    "Efficiency vs Overall Value",
                    "Player Efficiency Rating (PER)", "Value Over Replacement (VORP)", other_rows=other_candidate_rows),
                "caption": "SGA's efficiency numbers rival Jokic while playing on the conference's best team.",
                "x": "PER", "y": "VORP",
                "x_label": "Player Efficiency Rating (PER)", "y_label": "Value Over Replacement (VORP)"
            },
            {
                "fig": styled_scatter(df, "OWS", "VORP", row, color,
                    "Offensive Win Shares vs VORP",
                    "Offensive Win Shares (OWS)", "Value Over Replacement (VORP)", other_rows=other_candidate_rows),
                "caption": "His OWS lead the guard position — he single-handedly drives OKC's offense.",
                "x": "OWS", "y": "VORP",
                "x_label": "Offensive Win Shares (OWS)", "y_label": "Value Over Replacement (VORP)"
            },
            {
                "fig": styled_scatter(df, "PER", "OWS", row, color,
                    "PER vs Offensive Win Shares",
                    "Player Efficiency Rating (PER)", "Offensive Win Shares (OWS)", other_rows=other_candidate_rows),
                "caption": "Consistency and efficiency make SGA the most complete guard in the league.",
                "x": "PER", "y": "OWS",
                "x_label": "Player Efficiency Rating (PER)", "y_label": "Offensive Win Shares (OWS)"
            },
        ]
    return charts


def build_comparison_charts():
    keys = PLAYER_KEYS
    names = [players[k]["name"].split(" ")[-1] for k in keys]
    colors = [players[k]["color"] for k in keys]

    metrics = ["PER", "VORP", "OWS"]
    vals = []
    for k in keys:
        row = get_player_row(players[k]["search"])
        vals.append([row[m].values[0] if not row.empty and m in row.columns else 0 for m in metrics])

    figs = []

    # Chart 1: Bar chart — PER comparison
    fig1 = go.Figure(go.Bar(
        x=names,
        y=[v[0] for v in vals],
        marker_color=colors,
        text=[f"{v[0]:.1f}" for v in vals],
        textposition="outside",
        textfont=dict(color=WHITE, size=13)
    ))
    fig1.update_layout(
        title=dict(text="Player Efficiency Rating (PER)", font=dict(size=13, color=GOLD), x=0.5),
        yaxis_title="PER",
        **CHART_LAYOUT
    )
    figs.append((fig1, "PER measures overall per-minute production. Higher = more efficient."))

    # Chart 2: Bar chart — VORP
    fig2 = go.Figure(go.Bar(
        x=names,
        y=[v[1] for v in vals],
        marker_color=colors,
        text=[f"{v[1]:.1f}" for v in vals],
        textposition="outside",
        textfont=dict(color=WHITE, size=13)
    ))
    fig2.update_layout(
        title=dict(text="Value Over Replacement Player (VORP)", font=dict(size=13, color=GOLD), x=0.5),
        yaxis_title="VORP",
        **CHART_LAYOUT
    )
    figs.append((fig2, "VORP estimates how much better this player is than a replacement-level player."))

    # Chart 3: Radar chart
    fig3 = go.Figure()
    radar_metrics = ["PER", "VORP", "OWS", "DWS", "WS"]
    for i, k in enumerate(keys):
        row = get_player_row(players[k]["search"])
        r_vals = []
        for m in radar_metrics:
            if not row.empty and m in row.columns:
                r_vals.append(float(row[m].values[0]))
            else:
                r_vals.append(0)
        fig3.add_trace(go.Scatterpolar(
            r=r_vals + [r_vals[0]],
            theta=radar_metrics + [radar_metrics[0]],
            fill="toself",
            fillcolor=players[k]["color"] + "33",
            line=dict(color=players[k]["color"], width=2),
            name=players[k]["short"]
        ))
    fig3.update_layout(
        polar=dict(
            bgcolor="rgba(16,22,42,0.9)",
            radialaxis=dict(visible=True, color=GREY, gridcolor="#1E2640"),
            angularaxis=dict(color=TEXT, gridcolor="#1E2640")
        ),
        title=dict(text="Multi-Metric Radar Comparison", font=dict(size=13, color=GOLD), x=0.5),
        showlegend=True,
        legend=dict(font=dict(color=TEXT), bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        margin=dict(l=60, r=60, t=50, b=40)
    )
    figs.append((fig3, "Radar view shows each player's strengths and weaknesses across all key metrics."))

    return figs


# -----------------------------
# GLOBAL CSS
# -----------------------------
GLOBAL_STYLE = {
    "fontFamily": "'Georgia', serif",
    "background": BG,
    "minHeight": "100vh",
    "color": TEXT,
    "position": "relative",
    "overflow": "hidden"
}

# -----------------------------
# LAYOUT
# -----------------------------
app.layout = html.Div([
    dcc.Store(id="selected-player", data=None),
    dcc.Store(id="stage", data="select"),
    dcc.Store(id="selected-chart", data=None),

    # Background texture
    html.Div(style={
        "position": "fixed", "inset": "0", "zIndex": "0",
        "backgroundImage": "radial-gradient(ellipse at 20% 50%, #0D1B3E 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, #1A0D2E 0%, transparent 60%)",
        "pointerEvents": "none"
    }),

    html.Div([
        # HEADER
        html.Div([
            html.Div("NBA", style={
                "fontFamily": "'Georgia', serif",
                "fontSize": "11px",
                "letterSpacing": "6px",
                "color": GOLD,
                "marginBottom": "4px"
            }),
            html.H1(id="main-title", children="2026 MVP RACE", style={
                "fontFamily": "'Georgia', serif",
                "fontSize": "clamp(28px, 5vw, 52px)",
                "fontWeight": "900",
                "letterSpacing": "4px",
                "margin": "0",
                "color": WHITE,
                "textTransform": "uppercase"
            }),
            html.Div(id="subtitle", children="SELECT A CANDIDATE", style={
                "fontSize": "12px",
                "letterSpacing": "5px",
                "color": GREY,
                "marginTop": "6px"
            })
        ], style={"textAlign": "center", "padding": "40px 0 20px"}),

        # BACK BUTTON
        html.Button("← BACK", id="back-button", n_clicks=0, style={
            "display": "none",
            "position": "fixed",
            "top": "24px",
            "left": "24px",
            "background": "transparent",
            "border": "1px solid {GOLD}",
            "color": GOLD,
            "fontFamily": "'Georgia', serif",
            "fontSize": "11px",
            "letterSpacing": "3px",
            "padding": "10px 20px",
            "cursor": "pointer",
            "zIndex": "100",
            "transition": "all 0.3s"
        }),

        # MAIN CONTENT AREA
        html.Div(id="main-content"),

        # Hidden inputs for dynamic callback IDs
        html.Div([
            html.Button("", id="chart-0-btn", n_clicks=0, style={"display": "none"}),
            html.Button("", id="chart-1-btn", n_clicks=0, style={"display": "none"}),
            html.Button("", id="chart-2-btn", n_clicks=0, style={"display": "none"}),
            html.Button("", id="compare-btn", n_clicks=0, style={"display": "none"})
        ], style={"display": "none"})

    ], style={"position": "relative", "zIndex": "1", "maxWidth": "1400px", "margin": "0 auto", "padding": "0 24px"})

], style=GLOBAL_STYLE)


# -----------------------------
# STATE MACHINE
# -----------------------------
@app.callback(
    Output("selected-player", "data"),
    Output("stage", "data"),
    Output("selected-chart", "data"),
    Input("wemby-card", "n_clicks", allow_optional=True),
    Input("Jokic-card", "n_clicks", allow_optional=True),
    Input("shai-card", "n_clicks", allow_optional=True),
    Input("back-button", "n_clicks"),
    Input("chart-0-btn", "n_clicks", allow_optional=True),
    Input("chart-1-btn", "n_clicks", allow_optional=True),
    Input("chart-2-btn", "n_clicks", allow_optional=True),
    Input("compare-btn", "n_clicks", allow_optional=True),
    State("selected-player", "data"),
    State("stage", "data"),
    State("selected-chart", "data"),
    prevent_initial_call=True
)
def handle_state(w, j, s, back, c0, c1, c2, compare, selected, stage, sel_chart):
    triggered = ctx.triggered_id
    if not triggered:
        return selected, stage, sel_chart

    if triggered == "back-button":
        if stage == "advanced":
            return selected, "charts", None
        elif stage == "charts":
            return selected, "focus", None
        elif stage == "focus":
            return None, "select", None
        elif stage == "compare":
            return None, "select", None
        return selected, stage, sel_chart

    if triggered in ("wemby-card", "Jokic-card", "shai-card"):
        player_key = triggered.replace("-card", "")
        if stage == "select":
            return player_key, "focus", None
        if stage == "focus" and selected == player_key:
            return player_key, "charts", None
        return player_key, "focus", None

    if triggered in ("chart-0-btn", "chart-1-btn", "chart-2-btn"):
        chart_idx = int(triggered.replace("chart-", "").replace("-btn", ""))
        return selected, "advanced", chart_idx

    if triggered == "compare-btn":
        return selected, "compare", None

    return selected, stage, sel_chart


# -----------------------------
# TITLE / SUBTITLE
# -----------------------------
@app.callback(
    Output("main-title", "children"),
    Output("subtitle", "children"),
    Input("selected-player", "data"),
    Input("stage", "data")
)
def update_header(player, stage):
    if stage == "select":
        return "2026 MVP RACE", "SELECT A CANDIDATE"
    if stage == "focus" and player:
        return players[player]["short"], players[player]["team"].upper()
    if stage == "charts" and player:
        return players[player]["short"], "ADVANCED METRICS — CLICK A CHART TO EXPLORE"
    if stage == "advanced" and player:
        return players[player]["short"], "DEEP DIVE — CLICK COMPARE WHEN READY"
    if stage == "compare":
        return "HEAD TO HEAD", "THE THREE CANDIDATES COMPARED"
    return "2026 MVP RACE", "SELECT A CANDIDATE"


# -----------------------------
# BACK BUTTON VISIBILITY
# -----------------------------
@app.callback(
    Output("back-button", "style"),
    Input("stage", "data")
)
def toggle_back(stage):
    base = {
        "position": "fixed", "top": "24px", "left": "24px",
        "background": "transparent", "border": f"1px solid {GOLD}",
        "color": GOLD, "fontFamily": "'Georgia', serif",
        "fontSize": "11px", "letterSpacing": "3px",
        "padding": "10px 20px", "cursor": "pointer",
        "zIndex": "100", "transition": "all 0.3s"
    }
    if stage == "select":
        return {**base, "display": "none"}
    return {**base, "display": "block"}


# -----------------------------
# MAIN CONTENT
# -----------------------------
@app.callback(
    Output("main-content", "children"),
    Input("selected-player", "data"),
    Input("stage", "data"),
    Input("selected-chart", "data")
)
def render_content(player, stage, sel_chart):

    # ---- STEP 1: SELECT ----
    if stage == "select" or stage == "focus":
        cards = []
        for key in PLAYER_KEYS:
            p = players[key]
            is_selected = (stage == "focus" and player == key)
            is_dimmed = (stage == "focus" and player != key)

            card_style = {
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "cursor": "pointer",
                "padding": "20px",
                "borderRadius": "4px",
                "border": f"2px solid {p['color'] if is_selected else 'transparent'}",
                "background": f"rgba(16,22,42,{0.9 if is_selected else 0.4})",
                "transition": "all 0.5s ease",
                "transform": "scale(1.08)" if is_selected else ("scale(0.88)" if is_dimmed else "scale(1)"),
                "filter": "grayscale(90%) opacity(0.5)" if is_dimmed else "none",
                "boxShadow": f"0 0 40px {p['color']}55, 0 0 80px {p['color']}22" if is_selected else "none",
                "flex": "1",
                "maxWidth": "340px",
                "minWidth": "240px"
            }

            img_style = {
                "width": "200px",
                "height": "160px",
                "objectFit": "cover",
                "objectPosition": "top",
                "borderRadius": "2px",
                "display": "block",
                "marginBottom": "16px"
            }

            hint = html.Div(
                "CLICK AGAIN TO CONTINUE →" if is_selected else "CLICK TO SELECT",
                style={
                    "fontSize": "10px",
                    "letterSpacing": "3px",
                    "color": p["color"] if is_selected else GREY,
                    "marginTop": "8px"
                }
            )

            cards.append(
                html.Div([
                    html.Img(src=p["img"], style=img_style),
                    html.Div(p["short"], style={
                        "fontSize": "22px", "fontWeight": "900",
                        "letterSpacing": "4px", "color": WHITE,
                        "textAlign": "center"
                    }),
                    html.Div(p["team"], style={
                        "fontSize": "10px", "letterSpacing": "3px",
                        "color": GREY, "marginTop": "4px", "textAlign": "center"
                    }),
                    hint
                ], id=f"{key}-card", n_clicks=0, style=card_style)
            )

        return html.Div([
            html.Div(cards, style={
                "display": "flex",
                "justifyContent": "center",
                "gap": "24px",
                "flexWrap": "wrap",
                "padding": "20px 0 60px"
            }),
            html.Div("↑ THE THREE CANDIDATES FOR 2026 NBA MVP ↑", style={
                "textAlign": "center",
                "fontSize": "10px",
                "letterSpacing": "4px",
                "color": GREY,
                "paddingBottom": "20px"
            })
        ])

    # ---- STEP 2: CHARTS ----
    if stage == "charts" and player:
        p = players[player]
        charts_data = build_player_charts(player)

        chart_cards = []
        for i, chart_data in enumerate(charts_data):
            fig = chart_data["fig"]
            caption = chart_data["caption"]
            chart_cards.append(
                html.Div([
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False},
                        style={"height": "260px"}
                    ),
                    html.Div(caption, style={
                        "fontSize": "11px",
                        "color": GREY,
                        "fontStyle": "italic",
                        "padding": "8px 12px",
                        "borderTop": f"1px solid #1E2640"
                    }),
                    html.Button("EXPLORE →", id=f"chart-{i}-btn", n_clicks=0, style={
                        "width": "100%",
                        "background": "transparent",
                        "border": f"1px solid {p['color']}55",
                        "color": p["color"],
                        "fontFamily": "'Georgia', serif",
                        "fontSize": "10px",
                        "letterSpacing": "3px",
                        "padding": "10px",
                        "cursor": "pointer",
                        "transition": "all 0.3s"
                    })
                ], style={
                    "background": PANEL,
                    "border": f"1px solid #1E2640",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                    "flex": "1",
                    "minWidth": "280px"
                })
            )

        # Pad missing chart buttons so callbacks don't break
        for i in range(len(charts_data), 3):
            chart_cards.append(html.Div([
                html.Button("", id=f"chart-{i}-btn", n_clicks=0, style={"display": "none"})
            ]))

        return html.Div([
            # Small player portrait top-left
            html.Div([
                html.Img(src=p["img"], style={
                    "width": "80px", "height": "64px",
                    "objectFit": "cover", "objectPosition": "top",
                    "borderRadius": "2px",
                    "border": f"2px solid {p['color']}"
                }),
                html.Div([
                    html.Div(p["short"], style={
                        "fontSize": "18px", "fontWeight": "900",
                        "letterSpacing": "3px", "color": WHITE
                    }),
                    html.Div(p["argument"], style={
                        "fontSize": "12px", "color": GREY,
                        "fontStyle": "italic", "maxWidth": "500px",
                        "lineHeight": "1.5"
                    })
                ], style={"marginLeft": "16px"})
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "28px"}),

            # Charts
            html.Div(chart_cards, style={
                "display": "flex",
                "gap": "16px",
                "flexWrap": "wrap"
            }),

            html.Div("CLICK ANY CHART TO DIVE DEEPER", style={
                "textAlign": "center", "fontSize": "10px",
                "letterSpacing": "4px", "color": GREY,
                "padding": "20px 0 10px"
            })
        ], style={"padding": "10px 0 40px"})

    # ---- STEP 3: ADVANCED ----
    if stage == "advanced" and player is not None and sel_chart is not None:
        p = players[player]
        charts_data = build_player_charts(player)
        chart_info = charts_data[sel_chart]
        main_fig = chart_info["fig"]
        main_caption = chart_info["caption"]
        others = [(i, cd["fig"], cd["caption"]) for i, cd in enumerate(charts_data) if i != sel_chart]

        row = get_player_row(p["search"])
        color = p["color"]
        other_candidate_rows = []
        for key in PLAYER_KEYS:
            if key == player:
                continue
            other_row = get_player_row(players[key]["search"])
            if not other_row.empty:
                other_candidate_rows.append(other_row)
        other_candidate_rows = pd.concat(other_candidate_rows, ignore_index=True) if other_candidate_rows else pd.DataFrame()

        support_charts = build_cohort_charts(row, chart_info["x"], chart_info["y"], chart_info["x_label"], chart_info["y_label"], color, p["short"], other_candidate_rows)

        if len(support_charts) < 2:
            alt_charts = []
            # Win Shares breakdown
            if "OWS" in df.columns and "DWS" in df.columns and not row.empty:
                fig_ws = go.Figure()
                ows_val = float(row["OWS"].values[0])
                dws_val = float(row["DWS"].values[0])
                avg_ows = df["OWS"].mean()
                avg_dws = df["DWS"].mean()

                fig_ws.add_trace(go.Bar(
                    x=["Offensive WS", "Defensive WS"],
                    y=[ows_val, dws_val],
                    name=p["short"],
                    marker_color=color,
                    text=[f"{ows_val:.1f}", f"{dws_val:.1f}"],
                    textposition="outside",
                    textfont=dict(color=WHITE)
                ))
                fig_ws.add_trace(go.Bar(
                    x=["Offensive WS", "Defensive WS"],
                    y=[avg_ows, avg_dws],
                    name="League Avg",
                    marker_color=GREY,
                    text=[f"{avg_ows:.1f}", f"{avg_dws:.1f}"],
                    textposition="outside",
                    textfont=dict(color=GREY)
                ))
                fig_ws.update_layout(
                    title=dict(text="Win Shares vs League Average", font=dict(size=13, color=GOLD), x=0.5),
                    barmode="group",
                    showlegend=True,
                    legend=dict(font=dict(color=TEXT), bgcolor="rgba(0,0,0,0)"),
                    **CHART_LAYOUT
                )
                alt_charts.append((fig_ws, "Win shares above average indicate direct team impact."))

            metrics_to_rank = ["PER", "VORP", "OWS"]
            available = [m for m in metrics_to_rank if m in df.columns]
            if available and not row.empty:
                percentiles = []
                for m in available:
                    val = row[m].values[0]
                    pct = (df[m] < val).sum() / len(df) * 100
                    percentiles.append(pct)

                fig_pct = go.Figure(go.Bar(
                    x=available,
                    y=percentiles,
                    marker_color=[color] * len(available),
                    text=[f"{p:.0f}th" for p in percentiles],
                    textposition="outside",
                    textfont=dict(color=WHITE)
                ))
                theme = {k: v for k, v in CHART_LAYOUT.items() if k != "yaxis"}
                fig_pct.update_layout(
                    title=dict(text=f"{p['short']} League Percentile Rankings", font=dict(size=13, color=GOLD), x=0.5),
                    yaxis=dict(range=[0, 115], title="Percentile"),
                    showlegend=False,
                    **theme
                )
                alt_charts.append((fig_pct, f"{p['short']} ranks in the elite tier league-wide across all key metrics."))

            while len(alt_charts) < 2:
                alt_charts.append((go.Figure(), ""))

            support_charts = alt_charts

        right_charts = []
        for fig_r, cap_r in support_charts[:2]:
            right_charts.append(
                html.Div([
                    dcc.Graph(figure=fig_r, config={"displayModeBar": False}, style={"height": "220px"}),
                    html.Div(cap_r, style={
                        "fontSize": "11px", "color": GREY,
                        "fontStyle": "italic", "padding": "8px 12px"
                    })
                ], style={
                    "background": PANEL,
                    "border": f"1px solid #1E2640",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                    "marginBottom": "12px"
                })
            )

        compare_btn = html.Div([
            html.Button("COMPARE ALL CANDIDATES →", id="compare-btn", n_clicks=0, style={
                "background": f"linear-gradient(135deg, {GOLD} 0%, {GOLD_LIGHT} 100%)",
                "border": "none",
                "color": "#0A0E1A",
                "fontFamily": "'Georgia', serif",
                "fontSize": "12px",
                "fontWeight": "bold",
                "letterSpacing": "3px",
                "padding": "16px 40px",
                "cursor": "pointer",
                "borderRadius": "2px",
                "marginTop": "24px",
                "transition": "all 0.3s"
            })
        ], style={"textAlign": "center"})

        return html.Div([
            html.Div([
                # Left: main expanded chart (2x size, takes up 60% width)
                html.Div([
                    html.Div("SELECTED METRIC", style={
                        "fontSize": "10px", "letterSpacing": "4px",
                        "color": color, "marginBottom": "8px"
                    }),
                    dcc.Graph(
                        figure=main_fig,
                        config={"displayModeBar": True},
                        style={"height": "520px"}
                    ),
                    html.Div(main_caption, style={
                        "fontSize": "12px", "color": TEXT,
                        "fontStyle": "italic",
                        "padding": "12px 16px",
                        "background": PANEL,
                        "borderTop": f"2px solid {color}",
                        "lineHeight": "1.6"
                    })
                ], style={
                    "flex": "1.8",
                    "background": PANEL,
                    "border": f"1px solid {color}44",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                    "boxShadow": f"0 0 30px {color}22"
                }),

                # Right: supporting charts stacked vertically (two same-size charts)
                html.Div([
                    html.Div("SUPPORTING EVIDENCE", style={
                        "fontSize": "10px", "letterSpacing": "4px",
                        "color": GOLD, "marginBottom": "12px"
                    }),
                    html.Div([
                        *right_charts
                    ], style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "16px"
                    })
                ], style={
                    "flex": "1",
                    "paddingLeft": "16px",
                    "display": "flex",
                    "flexDirection": "column"
                })

            ], style={"display": "flex", "gap": "16px", "alignItems": "flex-start"}),

            compare_btn

        ], style={"padding": "10px 0 40px"})

    # ---- STEP 4: COMPARE ----
    if stage == "compare":
        comp_charts = build_comparison_charts()

        # Dummy compare-btn so callback IDs are always present
        dummy_compare = html.Div(html.Button("", id="compare-btn", n_clicks=0, style={"display": "none"}))

        chart_divs = []
        for i, (fig, caption) in enumerate(comp_charts):
            chart_divs.append(
                html.Div([
                    dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "300px"}),
                    html.Div(caption, style={
                        "fontSize": "11px", "color": GREY,
                        "fontStyle": "italic", "padding": "10px 14px",
                        "borderTop": "1px solid #1E2640"
                    })
                ], style={
                    "background": PANEL,
                    "border": "1px solid #1E2640",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                    "flex": "1",
                    "minWidth": "280px"
                })
            )

        # Mini player portraits
        portraits = []
        for key in PLAYER_KEYS:
            p = players[key]
            portraits.append(html.Div([
                html.Img(src=p["img"], style={
                    "width": "60px", "height": "48px",
                    "objectFit": "cover", "objectPosition": "top",
                    "borderRadius": "2px",
                    "border": f"2px solid {p['color']}"
                }),
                html.Div(p["short"], style={
                    "fontSize": "11px", "letterSpacing": "2px",
                    "color": p["color"], "marginTop": "6px",
                    "textAlign": "center"
                })
            ], style={"textAlign": "center"}))

        return html.Div([
            dummy_compare,
            # Dummy chart buttons to prevent callback errors
            html.Div([
                html.Button("", id="chart-0-btn", n_clicks=0, style={"display": "none"}),
                html.Button("", id="chart-1-btn", n_clicks=0, style={"display": "none"}),
                html.Button("", id="chart-2-btn", n_clicks=0, style={"display": "none"}),
            ]),

            html.Div([
                html.Div("THE CANDIDATES", style={
                    "fontSize": "10px", "letterSpacing": "4px",
                    "color": GOLD, "marginBottom": "16px"
                }),
                html.Div(portraits, style={
                    "display": "flex", "gap": "32px",
                    "justifyContent": "center", "marginBottom": "32px"
                }),
            ], style={"textAlign": "center"}),

            html.Div(chart_divs, style={
                "display": "flex", "gap": "16px", "flexWrap": "wrap"
            }),

            html.Div([
                html.Div("WHO DESERVES THE AWARD?", style={
                    "fontSize": "10px", "letterSpacing": "5px",
                    "color": GOLD, "marginBottom": "12px"
                }),
                html.Div(
                    "The data tells a story. Jokic leads in efficiency and value metrics. "
                    "Wembanyama contributes on both ends unlike anyone in history. "
                    "SGA drives the league's best team. The numbers are yours to interpret.",
                    style={
                        "fontSize": "14px", "color": TEXT,
                        "maxWidth": "600px", "margin": "0 auto",
                        "lineHeight": "1.8", "fontStyle": "italic"
                    }
                )
            ], style={"textAlign": "center", "padding": "40px 0 20px"})

        ], style={"padding": "10px 0 40px"})

    # Fallback: always render dummy IDs so callbacks don't crash
    return html.Div([
        html.Button("", id="compare-btn", n_clicks=0, style={"display": "none"}),
        html.Button("", id="chart-0-btn", n_clicks=0, style={"display": "none"}),
        html.Button("", id="chart-1-btn", n_clicks=0, style={"display": "none"}),
        html.Button("", id="chart-2-btn", n_clicks=0, style={"display": "none"}),
    ])


if __name__ == "__main__":
    app.run(debug=True)