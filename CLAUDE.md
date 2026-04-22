# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the dashboard

```bash
streamlit run dashboard.py
```

## Dependencies

Install with:
```bash
pip install streamlit pandas plotly
```

## Architecture

The project is a single-file Streamlit dashboard (`dashboard.py`) with no modules or backend — all logic lives in one script.

**Data flow:**
1. `load_data()` (cached via `@st.cache_data`) reads the three CSV files and returns `(cups, matches, players)` DataFrames.
2. Sidebar controls (`sel_years`, `sel_team`) produce filtered views (`cups_f`, `matches_f`, `players_f`) used throughout.
3. Four tabs render Plotly charts directly against the filtered DataFrames — no intermediate state.

**CSV schemas (1930–2014 data):**
- `WorldCups.csv` — one row per tournament: `Year, Country, Winner, Runners-Up, Third, Fourth, GoalsScored, QualifiedTeams, MatchesPlayed, Attendance`
- `WorldCupMatches.csv` — one row per match: `Year, Stage, Stadium, City, Home/Away Team Name, Home/Away Team Goals, MatchID, Home/Away Team Initials, Event` (Event encodes goal/card events as tokens like `G23`, `OG45`)
- `WorldCupPlayers.csv` — one row per player-match: `RoundID, MatchID, Team Initials, Coach Name, Line-up, Shirt Number, Player Name, Position, Event`

**Goal parsing (`_count_goals`):** counts `G\d+` tokens minus `OG\d+` (own goals) in the `Event` column.

**Stage normalization (`_simplify_stage`):** maps raw FIFA stage strings to six canonical Portuguese labels used for consistent chart ordering.

**Theme constants** (`T`, `GOLD`, `GREEN`, `RED`, `CSCALE`) are defined at module level and reused in every chart.
