import pandas as pd
import requests
import os
from pathlib import Path
from typing import Dict, Any, Optional

REEP_PEOPLE_URL = "https://raw.githubusercontent.com/withqwerty/reep/main/data/people.csv"
CACHE_FILE = Path("./data/soccerdata_cache/reep_people.csv")

# Pre-compiled mapping for key players in the 2026 fixture previews
# to avoid network dependency in offline runs
LOCAL_PLAYER_CROSSWALK = {
    "cody gakpo": {
        "reep_id": "reep_p_cody_gakpo",
        "name": "Cody Gakpo",
        "fbref_id": "92e10ee0",
        "transfermarkt_id": "518490",
        "sofascore_id": "848208",
        "opta_id": "243396",
        "fotmob_id": "908752"
    },
    "memphis depay": {
        "reep_id": "reep_p_memphis_depay",
        "name": "Memphis Depay",
        "fbref_id": "8f869ec0",
        "transfermarkt_id": "167869",
        "sofascore_id": "184852",
        "opta_id": "108390",
        "fotmob_id": "291913"
    },
    "donyell malen": {
        "reep_id": "reep_p_donyell_malen",
        "name": "Donyell Malen",
        "fbref_id": "893c5d6c",
        "transfermarkt_id": "326029",
        "sofascore_id": "796120",
        "opta_id": "220677",
        "fotmob_id": "672462"
    },
    "kaoru mitoma": {
        "reep_id": "reep_p_kaoru_mitoma",
        "name": "Kaoru Mitoma",
        "fbref_id": "7df4aa1d",
        "transfermarkt_id": "504849",
        "sofascore_id": "892976",
        "opta_id": "426176",
        "fotmob_id": "1064560"
    },
    "takefusa kubo": {
        "reep_id": "reep_p_takefusa_kubo",
        "name": "Takefusa Kubo",
        "fbref_id": "f516a2b8",
        "transfermarkt_id": "405668",
        "sofascore_id": "879204",
        "opta_id": "415849",
        "fotmob_id": "964724"
    },
    "wataru endo": {
        "reep_id": "reep_p_wataru_endo",
        "name": "Wataru Endo",
        "fbref_id": "a90df5f5",
        "transfermarkt_id": "165784",
        "sofascore_id": "180290",
        "opta_id": "107122",
        "fotmob_id": "260904"
    },
    "franck kessié": {
        "reep_id": "reep_p_franck_kessie",
        "name": "Franck Kessié",
        "fbref_id": "fb9aa806",
        "transfermarkt_id": "294808",
        "sofascore_id": "791231",
        "opta_id": "196347",
        "fotmob_id": "570997"
    },
    "sébastien haller": {
        "reep_id": "reep_p_sebastien_haller",
        "name": "Sébastien Haller",
        "fbref_id": "579737fa",
        "transfermarkt_id": "157499",
        "sofascore_id": "183492",
        "opta_id": "107380",
        "fotmob_id": "277154"
    },
    "moisés caicedo": {
        "reep_id": "reep_p_moises_caicedo",
        "name": "Moisés Caicedo",
        "fbref_id": "162595a9",
        "transfermarkt_id": "687626",
        "sofascore_id": "969695",
        "opta_id": "463428",
        "fotmob_id": "1037562"
    },
    "enner valencia": {
        "reep_id": "reep_p_enner_valencia",
        "name": "Enner Valencia",
        "fbref_id": "0ad32a18",
        "transfermarkt_id": "129577",
        "sofascore_id": "141208",
        "opta_id": "88439",
        "fotmob_id": "189498"
    },
    "alexander isak": {
        "reep_id": "reep_p_alexander_isak",
        "name": "Alexander Isak",
        "fbref_id": "8b4f3b7d",
        "transfermarkt_id": "349066",
        "sofascore_id": "825966",
        "opta_id": "218320",
        "fotmob_id": "698656"
    },
    "viktor gyökeres": {
        "reep_id": "reep_p_viktor_gyokeres",
        "name": "Viktor Gyökeres",
        "fbref_id": "4d50f822",
        "transfermarkt_id": "325658",
        "sofascore_id": "841381",
        "opta_id": "241512",
        "fotmob_id": "781254"
    },
    "ellyes skhiri": {
        "reep_id": "reep_p_ellyes_skhiri",
        "name": "Ellyes Skhiri",
        "fbref_id": "5a0b777a",
        "transfermarkt_id": "325178",
        "sofascore_id": "790956",
        "opta_id": "216503",
        "fotmob_id": "588498"
    },
    "hannibal mejbri": {
        "reep_id": "reep_p_hannibal_mejbri",
        "name": "Hannibal Mejbri",
        "fbref_id": "7d1b3260",
        "transfermarkt_id": "620316",
        "sofascore_id": "980894",
        "opta_id": "482650",
        "fotmob_id": "1079820"
    }
}

class PlayerEntityResolver:
    """
    Resolves player entities across data providers using the open-source 
    withqwerty/reep register weekly crosswalk.
    """
    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self.df: Optional[pd.DataFrame] = None
        
    def _download_registry(self) -> bool:
        """Download player mapping register from GitHub."""
        try:
            os.makedirs(self.cache_file.parent, exist_ok=True)
            response = requests.get(REEP_PEOPLE_URL, timeout=10)
            if response.status_code == 200:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                return True
        except Exception:
            pass
        return False

    def load_registry(self):
        """Loads the registry from local cache or downloads it if missing."""
        if not self.cache_file.exists():
            self._download_registry()
            
        if self.cache_file.exists():
            try:
                self.df = pd.read_csv(self.cache_file, low_memory=False)
            except Exception:
                self.df = None

    def resolve_player(self, player_name: str) -> Dict[str, Any]:
        """
        Resolves a player's ID mapping across Opta, FBref, Transfermarkt, and FotMob.
        """
        cleaned_name = player_name.lower().strip()
        
        # Check high-priority local mapping first
        if cleaned_name in LOCAL_PLAYER_CROSSWALK:
            return LOCAL_PLAYER_CROSSWALK[cleaned_name]
            
        # Try finding in the full withqwerty/reep database if loaded
        if self.df is not None:
            # Simple substring matching
            matches = self.df[self.df['name'].str.lower().str.contains(cleaned_name, na=False)]
            if not matches.empty:
                row = matches.iloc[0]
                return {
                    "reep_id": row.get("reep_id", ""),
                    "name": row.get("name", ""),
                    "fbref_id": row.get("fbref_id", ""),
                    "transfermarkt_id": row.get("transfermarkt_id", ""),
                    "sofascore_id": row.get("sofascore_id", ""),
                    "opta_id": row.get("opta_id", ""),
                    "fotmob_id": row.get("fotmob_id", "")
                }
                
        # Default fallback
        return {
            "reep_id": f"reep_p_{cleaned_name.replace(' ', '_')}",
            "name": player_name,
            "fbref_id": "unknown",
            "transfermarkt_id": "unknown",
            "sofascore_id": "unknown",
            "opta_id": "unknown",
            "fotmob_id": "unknown"
        }

if __name__ == "__main__":
    resolver = PlayerEntityResolver()
    resolver.load_registry()
    print("Resolving Cody Gakpo:", resolver.resolve_player("Cody Gakpo"))
    print("Resolving Kaoru Mitoma:", resolver.resolve_player("Kaoru Mitoma"))
