import json
import streamlit as st
import os

@st.cache_data(ttl=600)
def load_live_bracket_state() -> dict:
    bracket_path = "data/bracket/grid_state.json"
    if not os.path.exists(bracket_path):
        return {}

    with open(bracket_path, "r") as f:
        data = json.load(f)

    import subprocess
    TEAM_ID_TO_NAME = {
        "1": "Mexico", "2": "South Africa", "3": "South Korea", "4": "Czechia",
        "5": "Canada", "6": "Bosnia and Herzegovina", "7": "Qatar", "8": "Switzerland",
        "9": "Brazil", "10": "Morocco", "11": "Haiti", "12": "Scotland",
        "13": "United States", "14": "Paraguay", "15": "Australia", "16": "Turkiye",
        "17": "Germany", "18": "Curacao", "19": "Ivory Coast", "20": "Ecuador",
        "21": "Netherlands", "22": "Japan", "23": "Sweden", "24": "Tunisia",
        "25": "Belgium", "26": "Egypt", "27": "Iran", "28": "New Zealand",
        "29": "Spain", "30": "Cape Verde", "31": "Saudi Arabia", "32": "Uruguay",
        "33": "France", "34": "Senegal", "35": "Iraq", "36": "Norway",
        "37": "Argentina", "38": "Algeria", "39": "Austria", "40": "Jordan",
        "41": "Portugal", "42": "DR Congo", "43": "Uzbekistan", "44": "Colombia",
        "45": "England", "46": "Croatia", "47": "Ghana", "48": "Panama"
    }

    # 1. Fetch live group standings
    try:
        url_groups = "https://worldcup26.ir/get/groups"
        result_groups = subprocess.run(['curl', '-s', '-k', url_groups], capture_output=True, text=True, timeout=10)
        if result_groups.returncode == 0:
            api_data = json.loads(result_groups.stdout)
            groups_list = []
            if isinstance(api_data, dict) and "groups" in api_data:
                groups_list = api_data["groups"]
            elif isinstance(api_data, list):
                groups_list = api_data
                
            if groups_list:
                groups = []
                for group in groups_list:
                    group_name = f"Group {group.get('name', '')}"
                    standings = []
                    for t in group.get("teams", []):
                        team_id = str(t.get("team_id", ""))
                        team_name = TEAM_ID_TO_NAME.get(team_id)
                        if team_name:
                            standings.append({
                                "team": team_name,
                                "p": int(t.get("mp", 0)),
                                "w": int(t.get("w", 0)),
                                "d": int(t.get("d", 0)),
                                "l": int(t.get("l", 0)),
                                "gf": int(t.get("gf", 0)),
                                "ga": int(t.get("ga", 0)),
                                "gd": int(t.get("gd", 0)),
                                "pts": int(t.get("pts", 0))
                            })
                    # Sort standings by pts, then gd, then gf descending
                    standings.sort(key=lambda x: (x.get("pts", 0), x.get("gd", 0), x.get("gf", 0)), reverse=True)
                    groups.append({
                        "name": group_name,
                        "standings": standings
                    })
                data["groups"] = groups
    except Exception:
        pass

    # 2. Fetch live games and dynamically build knockout rounds
    try:
        url_games = "https://worldcup26.ir/get/games"
        result_games = subprocess.run(['curl', '-s', '-k', url_games], capture_output=True, text=True, timeout=15)
        if result_games.returncode == 0:
            api_games_data = json.loads(result_games.stdout)
            games_list = []
            if isinstance(api_games_data, dict) and "games" in api_games_data:
                games_list = api_games_data["games"]
            elif isinstance(api_games_data, list):
                games_list = api_games_data
                
            if games_list:
                game_map = {str(g.get("id")): g for g in games_list}
                
                # Define exact mapping of API match IDs to bracket grid layout positions
                r32_ids = ["74", "77", "73", "75", "83", "84", "81", "82", "76", "78", "79", "80", "86", "88", "85", "87"]
                r16_ids = ["89", "90", "93", "94", "91", "92", "95", "96"]
                qf_ids = ["97", "98", "99", "100"]
                sf_ids = ["101", "102"]
                final_id = "104"
                third_id = "103"
                
                def make_match(match_id, prefix):
                    g = game_map.get(match_id)
                    if not g:
                        return {"id": f"{prefix}_{match_id}", "team1": "???", "team2": "???", "score1": None, "score2": None, "winner": None}
                    
                    t1 = g.get("home_team_name_en") or g.get("home_team_label") or "???"
                    t2 = g.get("away_team_name_en") or g.get("away_team_label") or "???"
                    
                    TEAM_NAME_MAP = {
                        "Turkey": "Turkiye",
                        "Czech Republic": "Czechia",
                        "Curaçao": "Curacao",
                        "Democratic Republic of the Congo": "DR Congo"
                    }
                    t1 = TEAM_NAME_MAP.get(t1, t1)
                    t2 = TEAM_NAME_MAP.get(t2, t2)
                    
                    s1 = g.get("home_score")
                    s2 = g.get("away_score")
                    
                    winner = None
                    if g.get("finished") == "TRUE" or g.get("finished") is True:
                        w_id = str(g.get("winner_id"))
                        h_id = str(g.get("home_team_id"))
                        if w_id == h_id:
                            winner = t1
                        else:
                            winner = t2
                            
                    return {
                        "id": f"{prefix}_{match_id}",
                        "team1": t1,
                        "team2": t2,
                        "score1": int(s1) if s1 is not None and str(s1).isdigit() else None,
                        "score2": int(s2) if s2 is not None and str(s2).isdigit() else None,
                        "winner": winner
                    }
                
                data["rounds"] = [
                    {"name": "Round of 32", "matches": [make_match(mid, "r32") for mid in r32_ids]},
                    {"name": "Round of 16", "matches": [make_match(mid, "r16") for mid in r16_ids]},
                    {"name": "Quarterfinals", "matches": [make_match(mid, "qf") for mid in qf_ids]},
                    {"name": "Semifinals", "matches": [make_match(mid, "sf") for mid in sf_ids]},
                    {"name": "Final", "matches": [make_match(final_id, "f")]}
                ]
                data["third_place"] = make_match(third_id, "tp")
    except Exception:
        pass

    return data

def render_painters_tape_bracket():
    # Load bracket state
    data = load_live_bracket_state()
    if not data:
        st.warning("Bracket data not found.")
        return

    # CSS to simulate the wood wall, blue painter's tape, and off-white masking tape connectors
    css_content = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap');

    .bracket-board {
        background-color: #c1925a; /* Wood color */
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(255,255,255,0.08) 0%, rgba(0,0,0,0.2) 100%),
            repeating-linear-gradient(0deg, rgba(0,0,0,0.02) 0px, rgba(0,0,0,0.02) 2px, transparent 2px, transparent 20px),
            repeating-linear-gradient(90deg, rgba(0,0,0,0.02) 0px, rgba(0,0,0,0.02) 2px, transparent 2px, transparent 20px);
        padding: 30px 15px;
        border-radius: 12px;
        min-height: 1000px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: inset 0 0 60px rgba(0,0,0,0.4), 0 10px 30px rgba(0,0,0,0.3);
        font-family: 'Permanent Marker', cursive;
        position: relative;
        overflow-x: auto;
        box-sizing: border-box;
    }

    /* Column Styles */
    .left-groups, .right-groups {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 920px;
        width: 280px;
        z-index: 5;
    }

    .left-bracket, .right-bracket {
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 920px;
        width: 480px;
    }

    .bracket-round {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 100%;
        width: 105px;
        position: relative;
    }

    .center-column {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 920px;
        width: 130px;
        z-index: 5;
        position: relative;
    }

    /* Group Card Styles */
    .group-card {
        display: flex;
        gap: 3px;
        align-items: stretch;
        position: relative;
    }

    .right-groups .group-card {
        flex-direction: row-reverse;
    }

    .group-teams-box {
        background-color: #2b77c8; /* Blue tape */
        color: #0d0d0d; /* Black marker */
        padding: 6px 8px;
        border-radius: 2px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        width: 105px;
        font-size: 11px;
        transform: rotate(-0.5deg);
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .group-header {
        border-bottom: 2px dashed rgba(0,0,0,0.2);
        padding-bottom: 3px;
        margin-bottom: 4px;
        font-weight: bold;
        text-align: center;
        letter-spacing: 0.5px;
    }

    .group-team {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.3;
    }

    .group-stat-strip {
        background-color: #2b77c8;
        color: #0d0d0d;
        padding: 6px 3px;
        border-radius: 2px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        width: 26px;
        font-size: 10px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
    }

    .group-stat-header {
        border-bottom: 2px dashed rgba(0,0,0,0.2);
        padding-bottom: 3px;
        margin-bottom: 4px;
        width: 100%;
        font-weight: bold;
    }

    .group-stat-val {
        line-height: 1.3;
    }

    /* Matchup Styles */
    .matchup {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 80px;
        position: relative;
        z-index: 3;
    }

    .team-tape {
        background-color: #2b77c8; /* Blue tape */
        color: #0d0d0d; /* Black marker */
        font-size: 11px;
        padding: 3px 6px;
        margin: 2px 0;
        width: 90px;
        text-align: center;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.35);
        position: relative;
        transform: rotate(-1deg);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        /* Torn edge clip path */
        clip-path: polygon(1% 0, 99% 2%, 98% 97%, 2% 98%);
    }

    .team-tape:nth-child(even) {
        transform: rotate(1.5deg);
        clip-path: polygon(2% 1%, 98% 0, 99% 99%, 1% 96%);
    }

    .team-tape.winner {
        background-color: #1d5ba5;
        color: #ffffff;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* Champion and Center Column Styles */
    .champion-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 25px;
        position: relative;
    }

    .champion-tape {
        background-color: #f3c734; /* Gold/yellow painter's tape */
        color: #000;
        font-size: 15px;
        padding: 8px 20px;
        box-shadow: 3px 3px 7px rgba(0,0,0,0.4);
        transform: rotate(-2deg);
        text-align: center;
        border-radius: 2px;
        clip-path: polygon(2% 0, 98% 3%, 100% 97%, 0 100%);
        margin-bottom: 5px;
    }

    .champion-label {
        font-size: 11px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .final-label {
        background-color: rgba(244, 230, 181, 0.9);
        color: #000;
        font-size: 11px;
        padding: 2px 8px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        transform: rotate(1deg);
        margin-bottom: 15px;
    }

    /* Connecting Masking Tape Lines */
    .bracket-line-horizontal {
        background-color: #eae6cf; /* Off-white masking tape */
        height: 7px;
        width: 25px;
        position: absolute;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        z-index: 1;
    }

    .left-bracket .bracket-line-horizontal {
        right: -25px;
    }

    .right-bracket .bracket-line-horizontal {
        left: -25px;
    }

    .bracket-line-horizontal-left {
        background-color: #eae6cf;
        height: 7px;
        width: 25px;
        position: absolute;
        left: -25px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        z-index: 1;
    }

    .bracket-line-horizontal-right {
        background-color: #eae6cf;
        height: 7px;
        width: 25px;
        position: absolute;
        right: -25px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        z-index: 1;
    }

    .bracket-line-vertical {
        background-color: #eae6cf;
        width: 7px;
        position: absolute;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        z-index: 1;
    }

    .left-bracket .bracket-line-vertical {
        right: -25px;
    }

    .right-bracket .bracket-line-vertical {
        left: -25px;
    }

    /* Odd matchup vertical connector goes down */
    .matchup:nth-child(odd) .bracket-line-vertical {
        top: 50%;
    }

    /* Even matchup vertical connector goes up */
    .matchup:nth-child(even) .bracket-line-vertical {
        bottom: 50%;
    }

    /* Specific Heights for Round Vertical Spans */
    .r32-matchup .bracket-line-vertical {
        height: 59px;
    }

    .r16-matchup .bracket-line-vertical {
        height: 117px;
    }

    .qf-matchup .bracket-line-vertical {
        height: 233px;
    }

    /* Paper Tape Corners to hold items on the wall */
    .tape-corner-left {
        position: absolute;
        width: 14px;
        height: 6px;
        background-color: rgba(244, 230, 181, 0.85); /* beige paper tape */
        top: -3px;
        left: -5px;
        transform: rotate(-30deg);
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        z-index: 6;
    }

    .tape-corner-right {
        position: absolute;
        width: 14px;
        height: 6px;
        background-color: rgba(244, 230, 181, 0.85);
        bottom: -3px;
        right: -5px;
        transform: rotate(25deg);
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        z-index: 6;
    }

    .group-stat-strip .tape-corner-left {
        width: 10px;
        height: 5px;
        top: -2px;
        left: -3px;
    }

    .group-stat-strip .tape-corner-right {
        width: 10px;
        height: 5px;
        bottom: -2px;
        right: -3px;
    }

    .board-title {
        position: absolute;
        top: 25px;
        left: 50%;
        transform: translateX(-50%) rotate(-1deg);
        background-color: rgba(244, 230, 181, 0.95);
        color: #000;
        font-size: 26px;
        padding: 5px 35px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        z-index: 10;
        text-transform: uppercase;
        clip-path: polygon(1% 0, 99% 1%, 98% 98%, 0 99%);
    }

    .board-title::before {
        content: "";
        position: absolute;
        width: 35px;
        height: 15px;
        background-color: rgba(244, 230, 181, 0.8);
        top: -8px;
        left: -20px;
        transform: rotate(-40deg);
    }

    .board-title::after {
        content: "";
        position: absolute;
        width: 35px;
        height: 15px;
        background-color: rgba(244, 230, 181, 0.8);
        bottom: -8px;
        right: -20px;
        transform: rotate(-30deg);
    }
    </style>
    """

    # 1. Generate Group Standings HTML
    groups = data.get("groups", [])
    left_groups_html = '<div class="left-groups">'
    right_groups_html = '<div class="right-groups">'

    for idx, g in enumerate(groups):
        g_name = g.get("name", "GROUP")
        standings = g.get("standings", [])
        
        card_html = f"""
        <div class="group-card">
            <div class="group-teams-box">
                <div class="tape-corner-left"></div>
                <div class="tape-corner-right"></div>
                <div class="group-header">{g_name.upper()}</div>
        """
        for s in standings:
            card_html += f'<div class="group-team">{s["team"].upper()}</div>'
        card_html += '</div>'

        # P Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({-1 if idx % 2 == 0 else 1.2}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">P</div>
        """
        for s in standings:
            card_html += f'<div class="group-stat-val">{s.get("p", 0)}</div>'
        card_html += '</div>'

        # W Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({1.2 if idx % 2 == 0 else -1}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">W</div>
        """
        for s in standings:
            card_html += f'<div class="group-stat-val">{s.get("w", 0)}</div>'
        card_html += '</div>'

        # D Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({-1.2 if idx % 2 == 0 else 0.8}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">D</div>
        """
        for s in standings:
            card_html += f'<div class="group-stat-val">{s.get("d", 0)}</div>'
        card_html += '</div>'

        # L Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({0.8 if idx % 2 == 0 else -1.2}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">L</div>
        """
        for s in standings:
            card_html += f'<div class="group-stat-val">{s.get("l", 0)}</div>'
        card_html += '</div>'

        # GD Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({-1.5 if idx % 2 == 0 else 1}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">+/-</div>
        """
        for s in standings:
            gd_str = f"+{s['gd']}" if s['gd'] > 0 else str(s['gd'])
            card_html += f'<div class="group-stat-val">{gd_str}</div>'
        card_html += '</div>'

        # Pts Strip
        card_html += f"""
        <div class="group-stat-strip" style="transform: rotate({1 if idx % 2 == 0 else -1.5}deg);">
            <div class="tape-corner-left"></div>
            <div class="tape-corner-right"></div>
            <div class="group-stat-header">Pts</div>
        """
        for s in standings:
            card_html += f'<div class="group-stat-val">{s["pts"]}</div>'
        card_html += '</div>'
        card_html += '</div>'

        if idx < 6:
            left_groups_html += card_html
        else:
            right_groups_html += card_html

    left_groups_html += '</div>'
    right_groups_html += '</div>'

    # Helper function to render a single matchup cell
    def render_matchup_cell(match, round_class, has_prev_line=False, has_next_line=False, is_left_half=True):
        if not match:
            t1, t2, w = "???", "???", None
        else:
            t1 = match.get("team1") or "???"
            t2 = match.get("team2") or "???"
            w = match.get("winner")

        c1 = "team-tape winner" if w == t1 and t1 != "???" else "team-tape"
        c2 = "team-tape winner" if w == t2 and t2 != "???" else "team-tape"

        html = f'<div class="matchup {round_class}">'
        html += f'<div class="team-tape-wrapper"><div class="tape-corner-left"></div><div class="tape-corner-right"></div><div class="{c1}">{t1.upper()}</div></div>'
        html += f'<div class="team-tape-wrapper"><div class="tape-corner-left"></div><div class="tape-corner-right"></div><div class="{c2}">{t2.upper()}</div></div>'

        # Render lines
        if is_left_half:
            if has_next_line:
                html += '<div class="bracket-line-horizontal"></div><div class="bracket-line-vertical"></div>'
            if has_prev_line:
                html += '<div class="bracket-line-horizontal-left"></div>'
        else:
            if has_next_line:
                html += '<div class="bracket-line-horizontal"></div><div class="bracket-line-vertical"></div>'
            if has_prev_line:
                html += '<div class="bracket-line-horizontal-right"></div>'

        html += '</div>'
        return html

    # Extract Rounds
    rounds_data = data.get("rounds", [])
    r32 = rounds_data[0].get("matches", []) if len(rounds_data) > 0 else []
    r16 = rounds_data[1].get("matches", []) if len(rounds_data) > 1 else []
    qf = rounds_data[2].get("matches", []) if len(rounds_data) > 2 else []
    sf = rounds_data[3].get("matches", []) if len(rounds_data) > 3 else []
    final_match = rounds_data[4].get("matches", [{}])[0] if len(rounds_data) > 4 and len(rounds_data[4].get("matches", [])) > 0 else {}
    third_place = data.get("third_place", {})

    # 2. Left Bracket HTML
    left_bracket_html = '<div class="left-bracket">'
    
    # R32 Column (Left 8 matches)
    left_bracket_html += '<div class="bracket-round">'
    for m in r32[:8]:
        left_bracket_html += render_matchup_cell(m, "r32-matchup", has_prev_line=False, has_next_line=True, is_left_half=True)
    left_bracket_html += '</div>'

    # R16 Column (Left 4 matches)
    left_bracket_html += '<div class="bracket-round">'
    for m in r16[:4]:
        left_bracket_html += render_matchup_cell(m, "r16-matchup", has_prev_line=True, has_next_line=True, is_left_half=True)
    left_bracket_html += '</div>'

    # QF Column (Left 2 matches)
    left_bracket_html += '<div class="bracket-round">'
    for m in qf[:2]:
        left_bracket_html += render_matchup_cell(m, "qf-matchup", has_prev_line=True, has_next_line=True, is_left_half=True)
    left_bracket_html += '</div>'

    # SF Column (Left 1 match)
    left_bracket_html += '<div class="bracket-round">'
    for m in sf[:1]:
        left_bracket_html += render_matchup_cell(m, "sf-matchup", has_prev_line=True, has_next_line=True, is_left_half=True)
    left_bracket_html += '</div>'

    left_bracket_html += '</div>'

    # 3. Center Column HTML (Final & Third Place)
    f_t1 = final_match.get("team1") or "???"
    f_t2 = final_match.get("team2") or "???"
    f_w = final_match.get("winner")
    champion = f_w if f_w else "???"

    center_html = '<div class="center-column">'
    
    # Champion Display
    center_html += f"""
    <div class="champion-box">
        <div class="tape-corner-left" style="width: 25px; height: 10px; top: -7px;"></div>
        <div class="tape-corner-right" style="width: 25px; height: 10px; bottom: -7px;"></div>
        <div class="champion-tape">{champion.upper()}</div>
        <div class="champion-label">2026 World Cup Champion</div>
    </div>
    """

    center_html += '<div class="final-label">WORLD CUP FINAL</div>'

    # Final Matchup
    center_html += '<div class="matchup final-matchup" style="height: 100px;">'
    # Line left to Left SF
    center_html += '<div class="bracket-line-horizontal-left" style="width: 45px; left: -45px;"></div>'
    # Line right to Right SF
    center_html += '<div class="bracket-line-horizontal-right" style="width: 45px; right: -45px;"></div>'
    
    c1 = "team-tape winner" if f_w == f_t1 and f_t1 != "???" else "team-tape"
    c2 = "team-tape winner" if f_w == f_t2 and f_t2 != "???" else "team-tape"
    
    center_html += f'<div class="team-tape-wrapper"><div class="tape-corner-left"></div><div class="tape-corner-right"></div><div class="{c1}" style="width: 105px; font-size: 12px; padding: 5px 8px;">{f_t1.upper()}</div></div>'
    center_html += f'<div class="team-tape-wrapper"><div class="tape-corner-left"></div><div class="tape-corner-right"></div><div class="{c2}" style="width: 105px; font-size: 12px; padding: 5px 8px;">{f_t2.upper()}</div></div>'
    center_html += '</div>'

    # Third Place Matchup (if exists)
    if third_place:
        tp_t1 = third_place.get("team1") or "???"
        tp_t2 = third_place.get("team2") or "???"
        tp_w = third_place.get("winner")
        tp_c1 = "team-tape winner" if tp_w == tp_t1 and tp_t1 != "???" else "team-tape"
        tp_c2 = "team-tape winner" if tp_w == tp_t2 and tp_t2 != "???" else "team-tape"
        
        center_html += '<div style="margin-top: 40px; border-top: 2px dashed rgba(0,0,0,0.15); width: 100%; padding-top: 20px; display: flex; flex-direction: column; align-items: center;">'
        center_html += '<div class="final-label" style="font-size: 9px; padding: 1px 6px; margin-bottom: 8px;">THIRD PLACE PLAYOFF</div>'
        center_html += '<div class="matchup third-place-matchup">'
        center_html += f'<div class="team-tape-wrapper"><div class="tape-corner-left" style="width: 10px; height: 5px;"></div><div class="tape-corner-right" style="width: 10px; height: 5px;"></div><div class="{tp_c1}" style="width: 80px; font-size: 9px; padding: 2px 4px;">{tp_t1.upper()}</div></div>'
        center_html += f'<div class="team-tape-wrapper"><div class="tape-corner-left" style="width: 10px; height: 5px;"></div><div class="tape-corner-right" style="width: 10px; height: 5px;"></div><div class="{tp_c2}" style="width: 80px; font-size: 9px; padding: 2px 4px;">{tp_t2.upper()}</div></div>'
        center_html += '</div></div>'

    center_html += '</div>'

    # 4. Right Bracket HTML (reversed layout flow: SF -> QF -> R16 -> R32)
    right_bracket_html = '<div class="right-bracket">'
    
    # SF Column (Right 1 match: sf[1:])
    right_bracket_html += '<div class="bracket-round">'
    for m in sf[1:2]:
        right_bracket_html += render_matchup_cell(m, "sf-matchup", has_prev_line=True, has_next_line=True, is_left_half=False)
    right_bracket_html += '</div>'

    # QF Column (Right 2 matches: qf[2:])
    right_bracket_html += '<div class="bracket-round">'
    for m in qf[2:4]:
        right_bracket_html += render_matchup_cell(m, "qf-matchup", has_prev_line=True, has_next_line=True, is_left_half=False)
    right_bracket_html += '</div>'

    # R16 Column (Right 4 matches: r16[4:])
    right_bracket_html += '<div class="bracket-round">'
    for m in r16[4:8]:
        right_bracket_html += render_matchup_cell(m, "r16-matchup", has_prev_line=True, has_next_line=True, is_left_half=False)
    right_bracket_html += '</div>'

    # R32 Column (Right 8 matches: r32[8:])
    right_bracket_html += '<div class="bracket-round">'
    for m in r32[8:16]:
        right_bracket_html += render_matchup_cell(m, "r32-matchup", has_prev_line=False, has_next_line=True, is_left_half=False)
    right_bracket_html += '</div>'

    right_bracket_html += '</div>'

    # Assemble Full Board
    board_title = f'<div class="board-title">{data.get("tournament", "WORLD CUP 2026").upper()}</div>'
    
    html_content = f"""
    <div class="bracket-board">
        {board_title}
        {left_groups_html}
        {left_bracket_html}
        {center_html}
        {right_bracket_html}
        {right_groups_html}
    </div>
    """
    
    full_html = f"""
    {css_content}
    {html_content}
    """
    
    st.html(full_html)
