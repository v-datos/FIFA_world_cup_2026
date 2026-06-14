# Section 3: Static Data Reading Layer Implementation

When a user selects a match in the Streamlit frontend, your framework will skip the BigQuery query layer entirely and read the data directly from local storage:

```python
import streamlit as st
import json
from pathlib import Path

def load_local_match_metrics(match_id: int) -> dict:
    filepath = Path(f"./data/matches/{match_id}/metrics.json")
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# Execution within the Match Panel
match_data = load_local_match_metrics(selected_match_id)

if match_data:
    # Read metric structures into the frontend layout
    t1_stats = match_data["base_statistics"]["team1"]
    t2_stats = match_data["base_statistics"]["team2"]
    
    # Render using your existing visualization elements
    # create_pass_network(match_data["progressive_actions"]["team1"])
    # create_match_momentum_timeline(match_data["timelines"]["momentum"])
else:
    st.warning("Match analytical payload not generated yet.")