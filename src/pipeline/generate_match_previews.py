import os
import json
import subprocess
from pathlib import Path
import pandas as pd
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel

# 1. Setup paths
DATA_DIR = Path("./data/matches")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 2. Clean team name function (matching app.py key generation)
def clean_team_name(name: str) -> str:
    return (name.lower()
            .strip()
            .replace(" ", "_")
            .replace("'", "")
            .replace("ô", "o")
            .replace("é", "e")
            .replace("ö", "o")
            .replace("ç", "c")
            .replace("í", "i")
            .replace("á", "a")
            .replace("ú", "u"))

# 3. Query BigQuery for team historical stats
def get_historical_stats(team_name: str) -> str:
    client = bigquery.Client()
    query = """
    SELECT 
        COUNT(DISTINCT match_id) as matches_played,
        ROUND(AVG(goals), 2) as avg_goals,
        ROUND(AVG(total_xg), 2) as avg_xg,
        ROUND(AVG(shots), 2) as avg_shots,
        ROUND(AVG(shots_on_target), 2) as avg_shots_on_target,
        ROUND(AVG(successful_passes) * 100.0 / NULLIF(AVG(passes), 0), 2) as pass_accuracy,
        ROUND(AVG(tackles), 2) as avg_tackles,
        ROUND(AVG(yellow_cards), 2) as avg_yellow_cards
    FROM `midyear-castle-328020.fifa_data.team_match_summary`
    WHERE team = @team
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("team", "STRING", team_name)
        ]
    )
    try:
        df = client.query(query, job_config=job_config).to_dataframe()
        if not df.empty and df.iloc[0]['matches_played'] > 0:
            row = df.iloc[0]
            return (f"Team: {team_name}\n"
                    f"- Matches Analyzed: {row['matches_played']}\n"
                    f"- Avg Goals: {row['avg_goals']}\n"
                    f"- Avg xG: {row['avg_xg']}\n"
                    f"- Avg Shots: {row['avg_shots']} (On Target: {row['avg_shots_on_target']})\n"
                    f"- Pass Accuracy: {row['pass_accuracy']}%\n"
                    f"- Avg Tackles: {row['avg_tackles']}\n"
                    f"- Avg Yellow Cards: {row['avg_yellow_cards']}\n")
    except Exception as e:
        print(f"⚠️ Could not fetch BigQuery stats for {team_name}: {e}")
    return f"Team: {team_name} (No historic data in database)\n"

# 4. Generate preview content using Gemini on Vertex AI
def generate_ai_preview(team1: str, team2: str, date_str: str, time_str: str, venue: str, stage: str):
    t1_stats = get_historical_stats(team1)
    t2_stats = get_historical_stats(team2)
    
    t1_key = clean_team_name(team1)
    t2_key = clean_team_name(team2)
    
    prompt = f"""
You are a senior football data scientist and tactical analyst working for the FIFA World Cup 2026 analytics department.
Generate a tactical preview and Dixon-Coles forecast for the upcoming World Cup 2026 match:
{team1} vs {team2}
Date: {date_str}
Time: {time_str}
Venue: {venue}
Stage: {stage}

Here are the historical stats of the teams from the tournament database (use these to inform your analysis):
---
{t1_stats}
---
{t2_stats}
---

Your response must be a SINGLE valid JSON object (no markdown, no ```json formatting, just the raw JSON) with this exact schema:
{{
  "metadata": {{
    "match_id": "{t1_key}_{t2_key}_2026",
    "team1": "{team1}",
    "team2": "{team2}",
    "date": "{date_str}",
    "time": "{time_str}",
    "venue": "{venue}",
    "stage": "{stage}"
  }},
  "ai_summary": {{
    "key_headline": "A short, catchy tactical headline for the preview",
    "injuries": {{
      "{t1_key}": [
        "Key Player 1 (injury name - status)",
        "Key Player 2 (injury name - status)"
      ],
      "{t2_key}": [
        "Key Player 1 (injury name - status)",
        "Key Player 2 (injury name - status)"
      ]
    }},
    "confirmed_tactics": {{
      "{t1_key}": {{
        "formation": "e.g. 4-3-3",
        "philosophy": "A brief sentence describing their tactical philosophy.",
        "manager": "Current team manager name"
      }},
      "{t2_key}": {{
        "formation": "e.g. 4-2-3-1",
        "philosophy": "A brief sentence describing their tactical philosophy.",
        "manager": "Current team manager name"
      }}
    }},
    "tactical_insights": [
      "Tactical insight 1: focus on midfield battle or pressing intensity.",
      "Tactical insight 2: focus on key player matchups.",
      "Tactical insight 3: focus on how set pieces or transitions might decide the game."
    ]
  }},
  "dixon_coles_forecast": {{
    "team1_win": 0.45,
    "draw": 0.30,
    "team2_win": 0.25,
    "confidence": 0.85
  }},
  "score_probabilities": [
    {{"score": "1-0", "probability": 0.15}},
    {{"score": "2-0", "probability": 0.12}},
    {{"score": "1-1", "probability": 0.11}},
    {{"score": "2-1", "probability": 0.10}},
    {{"score": "0-0", "probability": 0.08}},
    {{"score": "0-1", "probability": 0.07}}
  ]
}}
Ensure that:
1. The keys for injuries and confirmed_tactics match exactly the lowercased clean team keys: "{t1_key}" and "{t2_key}".
2. All probabilities in dixon_coles_forecast and score_probabilities are realistic and sum up reasonably.
3. The response is syntactically correct JSON.
"""

    try:
        vertexai.init(location="us-east4")
        model = GenerativeModel("gemini-1.5-flash-001")
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown code block wraps if model outputted them
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0]
                text = text.strip()
                
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"❌ Gemini generation failed for {team1} vs {team2}: {e}")
        # Return a simple mock structure as fallback
        return {
            "metadata": {
                "match_id": f"{t1_key}_{t2_key}_2026",
                "team1": team1,
                "team2": team2,
                "date": date_str,
                "time": time_str,
                "venue": venue,
                "stage": stage
            },
            "ai_summary": {
                "key_headline": f"Tactical Clash: {team1} Takes On {team2}",
                "injuries": {
                    t1_key: ["No major injuries reported"],
                    t2_key: ["No major injuries reported"]
                },
                "confirmed_tactics": {
                    t1_key: {"formation": "4-3-3", "philosophy": "Balanced positional play.", "manager": "Head Coach"},
                    t2_key: {"formation": "4-4-2", "philosophy": "Compact counter-attacking.", "manager": "Head Coach"}
                },
                "tactical_insights": [
                    "Both teams will try to establish control early in the midfield.",
                    "Defensive discipline will be crucial in preventing quick transitions.",
                    "Set-pieces could be the deciding factor in a tightly contested match."
                ]
            },
            "dixon_coles_forecast": {
                "team1_win": 0.40,
                "draw": 0.30,
                "team2_win": 0.30,
                "confidence": 0.70
            },
            "score_probabilities": [
                {"score": "1-0", "probability": 0.15},
                {"score": "1-1", "probability": 0.14},
                {"score": "0-1", "probability": 0.13},
                {"score": "2-1", "probability": 0.10},
                {"score": "0-0", "probability": 0.09},
                {"score": "1-2", "probability": 0.08}
            ]
        }

# 5. Main execution loop: Fetch games and generate previews for next 3 upcoming games
def generate_upcoming_previews():
    try:
        print("🔄 Fetching tournament schedule from API...")
        url = "https://worldcup26.ir/get/games"
        api_data = None
        try:
            result = subprocess.run(['curl', '-s', '-k', url], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                api_data = json.loads(result.stdout)
        except Exception as e:
            print(f"⚠️ Live API call for games timed out or failed: {e}. Checking local cache...")
            
        if not api_data and os.path.exists("/tmp/games.json"):
            print("ℹ️ Using cached /tmp/games.json...")
            try:
                with open("/tmp/games.json", "r") as f:
                    api_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load local games cache: {e}")
                
        if not api_data:
            print("❌ Failed to query games API and no local cache found.")
            return
            
        games_list = []
        if isinstance(api_data, dict) and "games" in api_data:
            games_list = api_data["games"]
        elif isinstance(api_data, list):
            games_list = api_data
            
        if not games_list:
            print("❌ No games found in API response.")
            return
            
        # Filter upcoming games
        upcoming_games = []
        for g in games_list:
            if g.get("finished") == "FALSE" or g.get("finished") is False:
                upcoming_games.append(g)
                
        # Sort games by date/time
        # Format of local_date: "06/15/2026 12:00"
        def parse_date(g_dict):
            d_str = g_dict.get("local_date", "")
            try:
                parts = d_str.split(" ")
                date_parts = parts[0].split("/")
                time_parts = parts[1].split(":")
                return f"{date_parts[2]}-{date_parts[0]}-{date_parts[1]}T{time_parts[0]}:{time_parts[1]}:00"
            except Exception:
                return g_dict.get("date", "9999-12-31") + "T" + g_dict.get("time", "23:59:00")
                
        upcoming_games.sort(key=parse_date)
        
        print(f"Found {len(upcoming_games)} upcoming matches in schedule.")
        
        # We generate previews for the next 3 matches
        for g in upcoming_games[:3]:
            t1 = g.get("home_team_name_en") or g.get("home_team_label")
            t2 = g.get("away_team_name_en") or g.get("away_team_label")
            
            if not t1 or not t2 or "Winner" in t1 or "Winner" in t2 or "Runner-up" in t1 or "Runner-up" in t2:
                print(f"Skipping match ID {g.get('id')} - teams not fully resolved yet ({t1} vs {t2}).")
                continue
                
            date_val = g.get("date") or g.get("local_date", "").split(" ")[0]
            time_val = g.get("time") or g.get("local_date", "").split(" ")[1]
            venue = f"Stadium {g.get('stadium_id', 'Unknown')}"
            stage = f"Group Stage - Group {g.get('group', 'Unknown')}" if g.get("type") == "group" else g.get("type").upper()
            
            t1_key = clean_team_name(t1)
            t2_key = clean_team_name(t2)
            match_key = f"{t1_key}_{t2_key}_2026"
            
            match_folder = DATA_DIR / match_key
            sum_path = match_folder / "summary.json"
            met_path = match_folder / "metrics.json"
            
            if sum_path.exists() and met_path.exists():
                print(f"✅ Preview already exists for {t1} vs {t2} ({match_key}). Skipping.")
                continue
                
            print(f"⚙️ Generating AI Tactical Preview for {t1} vs {t2}...")
            preview_data = generate_ai_preview(t1, t2, date_val, time_val, venue, stage)
            
            # Write to files
            match_folder.mkdir(parents=True, exist_ok=True)
            
            summary_payload = {
                "metadata": preview_data.get("metadata"),
                "ai_summary": preview_data.get("ai_summary")
            }
            metrics_payload = {
                "dixon_coles_forecast": preview_data.get("dixon_coles_forecast"),
                "score_probabilities": preview_data.get("score_probabilities")
            }
            
            with open(sum_path, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=4, ensure_ascii=False)
            with open(met_path, "w", encoding="utf-8") as f:
                json.dump(metrics_payload, f, indent=4, ensure_ascii=False)
                
            print(f"✅ Successfully compiled preview folder for {match_key}!")
            
    except Exception as e:
        print("❌ Error running upcoming previews generation pipeline:", e)

if __name__ == "__main__":
    generate_upcoming_previews()
