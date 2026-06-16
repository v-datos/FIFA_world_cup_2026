import streamlit as st
import pandas as pd
from google.cloud import bigquery
import sys
import os
import json

# Add src/analytics to sys.path so we can import those modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'analytics')))

# Import custom modules for BigQuery
from fifa_metrics_bq import (
    get_match_stats_both_teams,
)
from fifa_visualizations_bq import (
    get_cached_shot_map,
    get_cached_pass_network,
    get_cached_touch_heatmap,
    get_cached_attacking_passes,
    create_xg_distribution_comparison,
    display_match_statistics,
    create_match_momentum_timeline,
    display_obv_breakdown,
    display_possession_adjusted_defensive_stats,
    create_match_radar_comparison,
    create_match_progressive_actions_map,
    create_match_playing_styles_scatter,
    get_cached_radar_chart,
)

# Import BigQuery helpers
from bigquery_helpers import get_bigquery_client, execute_query

from bracket_ui import render_painters_tape_bracket
from entity_resolution import PlayerEntityResolver
import importlib
import soccerdata_client
importlib.reload(soccerdata_client)
from soccerdata_client import SoccerDataClient

import translation_helper
importlib.reload(translation_helper)
from translation_helper import get_translation


ROSTERS_2026 = {
    "Netherlands": [
        "Cody Gakpo", "Memphis Depay", "Virgil van Dijk", "Nathan Aké", 
        "Matthijs de Ligt", "Denzel Dumfries", "Jeremie Frimpong", 
        "Stefan de Vrij", "Micky van de Ven", "Tijjani Reijnders", 
        "Jerdy Schouten", "Joey Veerman", "Xavi Simons", "Donyell Malen",
        "Wout Weghorst", "Brian Brobbey", "Joshua Zirkzee"
    ],
    "Japan": [
        "Kaoru Mitoma", "Takefusa Kubo", "Wataru Endo", "Hidemasa Morita", 
        "Daichi Kamada", "Ritsu Doan", "Takumi Minamino", "Keito Nakamura", 
        "Ko Itakura", "Koki Machida", "Shogo Taniguchi", "Yukinari Sugawara",
        "Zion Suzuki", "Ayase Ueda", "Daizen Maeda", "Takuma Asano"
    ],
    "Ivory Coast": [
        "Franck Kessié", "Sébastien Haller", "Simon Adingra", "Nicolas Pépé",
        "Ibrahim Sangaré", "Seko Fofana", "Odilon Kossounou", "Evan Ndicka",
        "Serge Aurier", "Yahia Fofana"
    ],
    "Ecuador": [
        "Moisés Caicedo", "Enner Valencia", "Piero Hincapié", "Pervis Estupiñán",
        "Willian Pacho", "Kendry Páez", "Jeremy Sarmiento", "Félix Torres",
        "Alexander Domínguez"
    ],
    "Sweden": [
        "Alexander Isak", "Dejan Kulusevski", "Viktor Gyökeres", "Emil Forsberg",
        "Victor Lindelöf", "Ludwig Augustinsson", "Robin Olsen", "Anthony Elanga",
        "Jens Cajuste"
    ],
    "Tunisia": [
        "Ellyes Skhiri", "Youssef Msakni", "Hannibal Mejbri", "Aissa Laïdouni",
        "Montassar Talbi", "Wajdi Kechrida", "Ali Abdi", "Bechir Ben Said",
        "Elias Achouri"
    ],
    "Spain": [
        "Lamine Yamal", "Nico Williams", "Rodri", "Pedri", "Dani Olmo", 
        "Álvaro Morata", "Dani Carvajal", "Robin Le Normand", "Unai Simón", "Fabián Ruiz"
    ],
    "Cape Verde": [
        "Ryan Mendes", "Garry Rodrigues", "Jovane Cabral", "Logan Costa", 
        "Bebé", "Jamiro Monteiro", "Kenny Rocha Santos", "Roberto Lopes"
    ],
    "Belgium": [
        "Kevin De Bruyne", "Romelu Lukaku", "Jérémy Doku", "Lois Openda", 
        "Leandro Trossard", "Amadou Onana", "Youri Tielemans", "Wout Faes", 
        "Timothy Castagne", "Koen Casteels"
    ],
    "Egypt": [
        "Mohamed Salah", "Mostafa Mohamed", "Omar Marmoush", "Trezeguet", 
        "Mohamed Elneny", "Emam Ashour", "Mohamed Hany", "Ahmed Hegazi", "Mohamed Abou Gabal"
    ],
    "Saudi Arabia": [
        "Salem Al-Dawsari", "Firas Al-Buraikan", "Abdulrahman Ghareeb", "Mohamed Kanno", 
        "Faisal Al-Ghamdi", "Saud Abdulhamid", "Ali Al-Bulaihi", "Yasser Al-Shahrani", "Mohammed Al-Owais"
    ],
    "Uruguay": [
        "Darwin Núñez", "Luis Suárez", "Federico Valverde", "Facundo Pellistri", 
        "Manuel Ugarte", "Nicolas de la Cruz", "Ronald Araújo", "Mathías Olivera", 
        "Jose María Giménez", "Sergio Rochet"
    ],
    "Iran": [
        "Mehdi Taremi", "Sardar Azmoun", "Alireza Jahanbakhsh", "Samon Ghoddos", 
        "Mehdi Ghayedi", "Saeid Ezatolahi", "Milad Mohammadi", "Shojae Khalilzadeh", "Alireza Beiranvand"
    ],
    "New Zealand": [
        "Chris Wood", "Sarpreet Singh", "Liberato Cacace", "Joe Bell", 
        "Marko Stamenic", "Tyler Bindon", "Michael Boxall", "Alex Paulsen"
    ],
    "France": [
        "Kylian Mbappé", "Antoine Griezmann", "Ousmane Dembélé", "Marcus Thuram", 
        "Bradley Barcola", "Aurélien Tchouaméni", "Eduardo Camavinga", "N'Golo Kanté", 
        "William Saliba", "Dayot Upamecano", "Theo Hernández", "Jules Koundé", "Mike Maignan"
    ],
    "Senegal": [
        "Sadio Mané", "Nicolas Jackson", "Ismaïla Sarr", "Iliman Ndiaye", 
        "Lamine Camara", "Pape Matar Sarr", "Kalidou Koulibaly", "Abdou Diallo", 
        "Moussa Niakhaté", "Édouard Mendy"
    ],
    "Iraq": [
        "Aymen Hussein", "Ali Jasim", "Mohanad Ali", "Ibrahim Bayesh", 
        "Youssef Amyn", "Amir Al-Ammari", "Osama Rashid", "Saad Natiq", 
        "Rebin Sulaka", "Jalal Hassan"
    ],
    "Norway": [
        "Erling Haaland", "Martin Ødegaard", "Alexander Sørloth", "Antonio Nusa", 
        "Oscar Bobb", "Sander Berge", "Patrick Berg", "Julian Ryerson", 
        "Leo Østigård", "Andreas Hanche-Olsen", "Ørjan Nyland"
    ],
    "Argentina": [
        "Lionel Messi", "Julián Álvarez", "Lautaro Martínez", "Ángel Di María", 
        "Rodrigo De Paul", "Alexis Mac Allister", "Enzo Fernández", "Leandro Paredes", 
        "Cristian Romero", "Lisandro Martínez", "Nicolás Otamendi", "Nahuel Molina", "Emiliano Martínez"
    ],
    "Algeria": [
        "Riyad Mahrez", "Baghdad Bounedjah", "Amine Gouiri", "Said Benrahma", 
        "Houssem Aouar", "Ismaël Bennacer", "Nabil Bentaleb", "Ramy Bensebaini", 
        "Aïssa Mandi", "Rayan Aït-Nouri", "Anthony Mandrea"
    ],
    "Austria": [
        "Marcel Sabitzer", "Konrad Laimer", "Christoph Baumgartner", "Romano Schmid", 
        "Michael Gregoritsch", "Florian Grillitsch", "Nicolas Seiwald", "Stefan Posch", 
        "Kevin Danso", "Maximilian Wöber", "Patrick Pentz"
    ],
    "Jordan": [
        "Musa Al-Taamari", "Yazan Al-Naimat", "Ali Olwan", "Mahmoud Al-Mardi", 
        "Nizar Al-Rashdan", "Noor Al-Rawabdeh", "Yazan Al-Arab", "Abdallah Nasib", 
        "Salem Al-Ajalin", "Yazid Abu Layla"
    ]
}

PLAYER_CLUBS_2026 = {
    # Netherlands
    "Cody Gakpo": "Liverpool",
    "Memphis Depay": "Corinthians",
    "Virgil van Dijk": "Liverpool",
    "Nathan Aké": "Manchester City",
    "Matthijs de Ligt": "Manchester United",
    "Denzel Dumfries": "Inter Milan",
    "Jeremie Frimpong": "Bayer Leverkusen",
    "Stefan de Vrij": "Inter Milan",
    "Micky van de Ven": "Tottenham Hotspur",
    "Tijjani Reijnders": "AC Milan",
    "Jerdy Schouten": "PSV Eindhoven",
    "Joey Veerman": "PSV Eindhoven",
    "Xavi Simons": "RB Leipzig",
    "Donyell Malen": "Borussia Dortmund",
    "Wout Weghorst": "Ajax",
    "Brian Brobbey": "Ajax",
    "Joshua Zirkzee": "Manchester United",
    
    # Japan
    "Kaoru Mitoma": "Brighton & Hove Albion",
    "Takefusa Kubo": "Real Sociedad",
    "Wataru Endo": "Liverpool",
    "Hidemasa Morita": "Sporting CP",
    "Daichi Kamada": "Crystal Palace",
    "Ritsu Doan": "SC Freiburg",
    "Takumi Minamino": "Monaco",
    "Keito Nakamura": "Reims",
    "Ko Itakura": "Borussia Mönchengladbach",
    "Koki Machida": "Union SG",
    "Shogo Taniguchi": "Sint-Truiden",
    "Yukinari Sugawara": "Southampton",
    "Zion Suzuki": "Parma",
    "Ayase Ueda": "Feyenoord",
    "Daizen Maeda": "Celtic",
    "Takuma Asano": "Mallorca",
    
    # Ivory Coast
    "Franck Kessié": "Al-Ahli",
    "Sébastien Haller": "Leganés",
    "Simon Adingra": "Brighton & Hove Albion",
    "Nicolas Pépé": "Villarreal",
    "Ibrahim Sangaré": "Nottingham Forest",
    "Seko Fofana": "Al-Ettifaq",
    "Odilon Kossounou": "Atalanta",
    "Evan Ndicka": "Roma",
    "Serge Aurier": "Galatasaray",
    "Yahia Fofana": "Angers",
    
    # Ecuador
    "Moisés Caicedo": "Chelsea",
    "Enner Valencia": "Internacional",
    "Piero Hincapié": "Bayer Leverkusen",
    "Pervis Estupiñán": "Brighton & Hove Albion",
    "Willian Pacho": "Paris Saint-Germain",
    "Kendry Páez": "Independiente del Valle",
    "Jeremy Sarmiento": "Burnley",
    "Félix Torres": "Corinthians",
    "Alexander Domínguez": "LDU Quito",
    
    # Sweden
    "Alexander Isak": "Newcastle United",
    "Dejan Kulusevski": "Tottenham Hotspur",
    "Viktor Gyökeres": "Sporting CP",
    "Emil Forsberg": "New York Red Bulls",
    "Victor Lindelöf": "Manchester United",
    "Ludwig Augustinsson": "Anderlecht",
    "Robin Olsen": "Aston Villa",
    "Anthony Elanga": "Nottingham Forest",
    "Jens Cajuste": "Ipswich Town",
    
    # Tunisia
    "Ellyes Skhiri": "Eintracht Frankfurt",
    "Youssef Msakni": "Al-Arabi",
    "Hannibal Mejbri": "Burnley",
    "Aissa Laïdouni": "Al-Wakrah",
    "Montassar Talbi": "Lorient",
    "Wajdi Kechrida": "Standard Liège",
    "Ali Abdi": "Nice",
    "Bechir Ben Said": "Espérance de Tunis",
    "Elias Achouri": "Copenhagen",
    
    # Spain
    "Lamine Yamal": "Barcelona",
    "Nico Williams": "Athletic Bilbao",
    "Rodri": "Manchester City",
    "Pedri": "Barcelona",
    "Dani Olmo": "Barcelona",
    "Álvaro Morata": "AC Milan",
    "Dani Carvajal": "Real Madrid",
    "Robin Le Normand": "Atlético Madrid",
    "Unai Simón": "Athletic Bilbao",
    "Fabián Ruiz": "Paris Saint-Germain",
    
    # Cape Verde
    "Ryan Mendes": "Kocaelispor",
    "Garry Rodrigues": "Sivasspor",
    "Jovane Cabral": "Estrela da Amadora",
    "Logan Costa": "Villarreal",
    "Bebé": "Racing Ferrol",
    "Jamiro Monteiro": "PEC Zwolle",
    "Kenny Rocha Santos": "AEZ Zakakiou",
    "Roberto Lopes": "Shamrock Rovers",
    
    # Belgium
    "Kevin De Bruyne": "Manchester City",
    "Romelu Lukaku": "Napoli",
    "Jérémy Doku": "Manchester City",
    "Lois Openda": "RB Leipzig",
    "Leandro Trossard": "Arsenal",
    "Amadou Onana": "Aston Villa",
    "Youri Tielemans": "Aston Villa",
    "Wout Faes": "Leicester City",
    "Timothy Castagne": "Fulham",
    "Koen Casteels": "Al-Qadsiah",
    
    # Egypt
    "Mohamed Salah": "Liverpool",
    "Mostafa Mohamed": "Nantes",
    "Omar Marmoush": "Eintracht Frankfurt",
    "Trezeguet": "Al-Rayyan",
    "Mohamed Elneny": "Al-Jazira",
    "Emam Ashour": "Al Ahly",
    "Mohamed Hany": "Al Ahly",
    "Ahmed Hegazi": "Neom",
    "Mohamed Abou Gabal": "National Bank of Egypt",
    
    # Saudi Arabia
    "Salem Al-Dawsari": "Al-Hilal",
    "Firas Al-Buraikan": "Al-Ahli",
    "Abdulrahman Ghareeb": "Al-Nassr",
    "Mohamed Kanno": "Al-Hilal",
    "Faisal Al-Ghamdi": "Beerschot",
    "Saud Abdulhamid": "Roma",
    "Ali Al-Bulaihi": "Al-Hilal",
    "Yasser Al-Shahrani": "Al-Hilal",
    "Mohammed Al-Owais": "Al-Hilal",
    
    # Uruguay
    "Darwin Núñez": "Liverpool",
    "Luis Suárez": "Inter Miami",
    "Federico Valverde": "Real Madrid",
    "Facundo Pellistri": "Panathinaikos",
    "Manuel Ugarte": "Manchester United",
    "Nicolas de la Cruz": "Flamengo",
    "Ronald Araújo": "Barcelona",
    "Mathías Olivera": "Napoli",
    "Jose María Giménez": "Atlético Madrid",
    "Sergio Rochet": "Internacional",
    
    # Iran
    "Mehdi Taremi": "Inter Milan",
    "Sardar Azmoun": "Shabab Al-Ahli",
    "Alireza Jahanbakhsh": "Heerenveen",
    "Samon Ghoddos": "Ittihad Kalba",
    "Mehdi Ghayedi": "Ittihad Kalba",
    "Saeid Ezatolahi": "Shabab Al-Ahli",
    "Milad Mohammadi": "Persepolis",
    "Shojae Khalilzadeh": "Tractor",
    "Alireza Beiranvand": "Tractor",
    
    # New Zealand
    "Chris Wood": "Nottingham Forest",
    "Sarpreet Singh": "Unattached",
    "Liberato Cacace": "Empoli",
    "Joe Bell": "Viking",
    "Marko Stamenic": "Olympiacos",
    "Tyler Bindon": "Reading",
    "Michael Boxall": "Minnesota United",
    "Alex Paulsen": "Auckland FC",

    # France
    "Kylian Mbappé": "Real Madrid",
    "Antoine Griezmann": "Atlético Madrid",
    "Ousmane Dembélé": "Paris Saint-Germain",
    "Marcus Thuram": "Inter Milan",
    "Bradley Barcola": "Paris Saint-Germain",
    "Aurélien Tchouaméni": "Real Madrid",
    "Eduardo Camavinga": "Real Madrid",
    "N'Golo Kanté": "Al-Ittihad",
    "William Saliba": "Arsenal",
    "Dayot Upamecano": "Bayern Munich",
    "Theo Hernández": "AC Milan",
    "Jules Koundé": "Barcelona",
    "Mike Maignan": "AC Milan",

    # Senegal
    "Sadio Mané": "Al-Nassr",
    "Nicolas Jackson": "Chelsea",
    "Ismaïla Sarr": "Crystal Palace",
    "Iliman Ndiaye": "Everton",
    "Lamine Camara": "Monaco",
    "Pape Matar Sarr": "Tottenham Hotspur",
    "Kalidou Koulibaly": "Al-Hilal",
    "Abdou Diallo": "Al-Arabi",
    "Moussa Niakhaté": "Lyon",
    "Édouard Mendy": "Al-Ahli",

    # Iraq
    "Aymen Hussein": "Al-Khor",
    "Ali Jasim": "Como",
    "Mohanad Ali": "Al-Shorta",
    "Ibrahim Bayesh": "Al-Riyadh",
    "Youssef Amyn": "Al-Wehda",
    "Amir Al-Ammari": "Cracovia",
    "Osama Rashid": "Free Agent",
    "Saad Natiq": "Al-Shorta",
    "Rebin Sulaka": "FC Seoul",
    "Jalal Hassan": "Al-Zawraa",

    # Norway
    "Erling Haaland": "Manchester City",
    "Martin Ødegaard": "Arsenal",
    "Alexander Sørloth": "Atlético Madrid",
    "Antonio Nusa": "RB Leipzig",
    "Oscar Bobb": "Manchester City",
    "Sander Berge": "Fulham",
    "Patrick Berg": "Bodø/Glimt",
    "Julian Ryerson": "Borussia Dortmund",
    "Leo Østigård": "Rennes",
    "Andreas Hanche-Olsen": "Mainz 05",
    "Ørjan Nyland": "Sevilla",

    # Argentina
    "Lionel Messi": "Inter Miami",
    "Julián Álvarez": "Atlético Madrid",
    "Lautaro Martínez": "Inter Milan",
    "Ángel Di María": "Benfica",
    "Rodrigo De Paul": "Atlético Madrid",
    "Alexis Mac Allister": "Liverpool",
    "Enzo Fernández": "Chelsea",
    "Leandro Paredes": "AS Roma",
    "Cristian Romero": "Tottenham Hotspur",
    "Lisandro Martínez": "Manchester United",
    "Nicolás Otamendi": "Benfica",
    "Nahuel Molina": "Atlético Madrid",
    "Emiliano Martínez": "Aston Villa",

    # Algeria
    "Riyad Mahrez": "Al-Ahli",
    "Baghdad Bounedjah": "Al-Shamal",
    "Amine Gouiri": "Rennes",
    "Said Benrahma": "Lyon",
    "Houssem Aouar": "Al-Ittihad",
    "Ismaël Bennacer": "AC Milan",
    "Nabil Bentaleb": "Lille",
    "Ramy Bensebaini": "Borussia Dortmund",
    "Aïssa Mandi": "Lille",
    "Rayan Aït-Nouri": "Wolverhampton Wanderers",
    "Anthony Mandrea": "Caen",

    # Austria
    "Marcel Sabitzer": "Borussia Dortmund",
    "Konrad Laimer": "Bayern Munich",
    "Christoph Baumgartner": "RB Leipzig",
    "Romano Schmid": "Werder Bremen",
    "Michael Gregoritsch": "SC Freiburg",
    "Florian Grillitsch": "TSG Hoffenheim",
    "Nicolas Seiwald": "RB Leipzig",
    "Stefan Posch": "Bologna",
    "Kevin Danso": "Lens",
    "Maximilian Wöber": "Leeds United",
    "Patrick Pentz": "Brøndby",

    # Jordan
    "Musa Al-Taamari": "Montpellier",
    "Yazan Al-Naimat": "Al-Ahli SC",
    "Ali Olwan": "Selangor",
    "Mahmoud Al-Mardi": "Al-Hussein Irbid",
    "Nizar Al-Rashdan": "Emirates Club",
    "Noor Al-Rawabdeh": "Selangor",
    "Yazan Al-Arab": "FC Seoul",
    "Abdallah Nasib": "Al-Hussein Irbid",
    "Salem Al-Ajalin": "Al-Faisaly",
    "Yazid Abu Layla": "Al-Jabalain"
}

LAST_TOURNAMENT_STANDINGS_2026 = {
    "Netherlands": "Semi-finals (UEFA Euro 2024)",
    "Japan": "Round of 16 (FIFA World Cup 2022)",
    "Ivory Coast": "Champions (Africa Cup of Nations 2023)",
    "Ecuador": "Quarter-finals (Copa América 2024)",
    "Sweden": "Round of 16 (UEFA Euro 2020)",
    "Tunisia": "Group Stage (Africa Cup of Nations 2023)",
    "Spain": "Champions (UEFA Euro 2024)",
    "Cape Verde": "Quarter-finals (Africa Cup of Nations 2023)",
    "Belgium": "Round of 16 (UEFA Euro 2024)",
    "Egypt": "Round of 16 (Africa Cup of Nations 2023)",
    "Saudi Arabia": "Round of 16 (AFC Asian Cup 2023)",
    "Uruguay": "Third Place (Copa América 2024)",
    "Iran": "Semi-finals (AFC Asian Cup 2023)",
    "New Zealand": "Champions (OFC Nations Cup 2024)",
    "France": "Runners-up (FIFA World Cup 2022)",
    "Senegal": "Round of 16 (Africa Cup of Nations 2023)",
    "Iraq": "Round of 16 (AFC Asian Cup 2023)",
    "Norway": "Group Stage (UEFA Nations League A 2024)",
    "Argentina": "Champions (FIFA World Cup 2022) / Champions (Copa América 2024)",
    "Algeria": "Group Stage (Africa Cup of Nations 2023)",
    "Austria": "Round of 16 (UEFA Euro 2024)",
    "Jordan": "Runners-up (AFC Asian Cup 2023)"
}

MATCH_VISUALIZATION_PROXIES = {
    "Netherlands": {"match_id": 3930180, "team": "Netherlands", "label": "UEFA Euro 2024"},
    "Japan": {"match_id": 3857255, "team": "Japan", "label": "FIFA World Cup 2022"},
    "Ivory Coast": {"match_id": 3922838, "team": "Côte d'Ivoire", "label": "Africa Cup of Nations 2023"},
    "Ecuador": {"match_id": 3939980, "team": "Ecuador", "label": "Copa América 2024"},
    "Sweden": {"match_id": 3788750, "team": "Sweden", "label": "UEFA Euro 2020"},
    "Tunisia": {"match_id": 3920404, "team": "Tunisia", "label": "Africa Cup of Nations 2023"},
    "France": {"match_id": 3930173, "team": "France", "label": "UEFA Euro 2024"},
    "Senegal": {"match_id": 3920412, "team": "Senegal", "label": "Africa Cup of Nations 2023"},
    "Argentina": {"match_id": 3942785, "team": "Argentina", "label": "Copa América 2024"},
    "Algeria": {"match_id": 3920390, "team": "Algeria", "label": "Africa Cup of Nations 2023"},
    "Austria": {"match_id": 3930180, "team": "Austria", "label": "UEFA Euro 2024"},
    "Norway": {"match_id": 3788750, "team": "Sweden", "label": "UEFA Euro 2020 (Proxy)"},
    "Iraq": {"match_id": 3920404, "team": "Tunisia", "label": "Arab Cup 2021 (Proxy)"},
    "Jordan": {"match_id": 3920404, "team": "Tunisia", "label": "Arab Cup 2021 (Proxy)"}
}


# Page Configuration
st.set_page_config(
    page_title="FIFA World Cup 2026 Dashboard",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Play fonts
def load_custom_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Play:wght@400;700&display=swap');
            html, body, [class*="css"], .stApp {
                font-family: 'Play', sans-serif !important;
            }
            </style>
        """, unsafe_allow_html=True)


# Custom HTML/CSS rendering helpers for premium stats cards
def render_player_cards_html(players):
    html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; width: 100%; font-family: \'Play\', sans-serif;">'
    for p in players:
        name = p.get("name", "Unknown Player")
        reep_id = p.get("reep_id", "N/A")
        fbref_id = p.get("fbref_id", "unknown")
        opta_id = p.get("opta_id", "unknown")
        fotmob_id = p.get("fotmob_id", "unknown")
        sofascore_id = p.get("sofascore_id", "unknown")
        tm_id = p.get("transfermarkt_id", "unknown")
        
        def badge_style(val, bg, border, text_color):
            if not val or str(val).lower() in ("unknown", "nan", "none", ""):
                return "background-color: #1f2937; color: #6b7280; border: 1px dashed #374151;"
            return f"background-color: {bg}; color: {text_color}; border: 1px solid {border};"

        fbref_style = badge_style(fbref_id, "#1e3a8a", "#2563eb", "#93c5fd")
        opta_style = badge_style(opta_id, "#312e81", "#4f46e5", "#c7d2fe")
        fotmob_style = badge_style(fotmob_id, "#064e3b", "#059669", "#6ee7b7")
        sofascore_style = badge_style(sofascore_id, "#701a75", "#d946ef", "#f5d0fe")
        tm_style = badge_style(tm_id, "#78350f", "#d97706", "#fde68a")

        def disp(val):
            if not val or str(val).lower() in ("unknown", "nan", "none", ""):
                return "Not Resolved"
            return str(val)

        html += f"""
        <div style="
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="font-weight: bold; font-size: 1.2rem; color: #fff; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span>👤 {name}</span>
                </div>
                <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 12px; background-color: #111827; padding: 2px 6px; border-radius: 4px; display: inline-block;">
                    Reep ID: {reep_id}
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">
                    <div style="{fbref_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">FBref</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(fbref_id)}</div>
                    </div>
                    <div style="{opta_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">Opta</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(opta_id)}</div>
                    </div>
                    <div style="{fotmob_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">FotMob</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(fotmob_id)}</div>
                    </div>
                    <div style="{sofascore_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">SofaScore</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(sofascore_id)}</div>
                    </div>
                    <div style="{tm_style} grid-column: span 2; padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">Transfermarkt</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(tm_id)}</div>
                    </div>
                </div>
            </div>
        </div>
        """
    html += '</div>'
    return html.replace('\n', ' ')

def render_score_probabilities_html(score_probs):
    if not score_probs:
        return """
        <div style="
            background: linear-gradient(145deg, #111827, #1f2937);
            border: 1px solid #374151;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-family: 'Play', sans-serif;
            text-align: center;
            color: #9ca3af;
            font-weight: bold;
        ">
            N/A (Forecast data unavailable)
        </div>
        """.replace('\n', ' ')

    max_prob = max(item["probability"] for item in score_probs) if score_probs else 1.0
    html = """
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
    """
    for item in score_probs:
        score = item["score"]
        prob = item["probability"]
        prob_pct = f"{prob * 100:.1f}%"
        bar_width = (prob / max_prob) * 100 if max_prob > 0 else 0
        html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="
                width: 70px; 
                background-color: #1f2937; 
                border: 1px solid #4b5563; 
                border-radius: 6px; 
                padding: 4px 8px; 
                text-align: center; 
                font-weight: bold; 
                color: #fff; 
                font-size: 0.95rem;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
            ">
                {score}
            </div>
            <div style="flex-grow: 1; margin: 0 16px; background-color: #374151; height: 10px; border-radius: 5px; overflow: hidden; position: relative;">
                <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); width: {bar_width}%; height: 100%; border-radius: 5px;"></div>
            </div>
            <div style="width: 60px; text-align: right; font-weight: bold; color: #10b981; font-size: 1rem;">
                {prob_pct}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def render_squad_comparison_html(team1_name, team2_name, neth, jap, elo1, elo2, left_color="#00c6ff", right_color="#ff007f", lang="English"):
    if not isinstance(neth, dict):
        neth = {}
    if not isinstance(jap, dict):
        jap = {}
        
    def fmt(d, key, fmt_spec, suffix=""):
        val = d.get(key)
        if val is None or val == "N/A" or val == "":
            return "N/A"
        try:
            formatted = ("{:" + fmt_spec + "}").format(val)
            if lang == "Español":
                if suffix == " yrs":
                    suffix = " años"
            return f"{formatted}{suffix}"
        except Exception:
            return "N/A"

    metrics = [
        {"label": get_translation("Squad Market Value", lang), "val1": fmt(neth, "squad_market_value_m", ".1f", "M") if neth.get("squad_market_value_m") is not None else "N/A", "val2": fmt(jap, "squad_market_value_m", ".1f", "M") if jap.get("squad_market_value_m") is not None else "N/A"},
        {"label": get_translation("Average Age", lang), "val1": fmt(neth, "average_age", ".1f", " yrs"), "val2": fmt(jap, "average_age", ".1f", " yrs")},
        {"label": get_translation("Club Elo Rating", lang), "val1": f"{elo1}" if elo1 is not None else "N/A", "val2": f"{elo2}" if elo2 is not None else "N/A"},
        {"label": get_translation("Goals / 90", lang), "val1": fmt(neth, "goals_per_90", ".2f"), "val2": fmt(jap, "goals_per_90", ".2f")},
        {"label": get_translation("Goals Conceded / 90", lang), "val1": fmt(neth, "goals_conceded_per_90", ".2f"), "val2": fmt(jap, "goals_conceded_per_90", ".2f")},
        {"label": get_translation("Expected Goals (xG) / 90", lang), "val1": fmt(neth, "expected_goals_per_90", ".2f"), "val2": fmt(jap, "expected_goals_per_90", ".2f")},
        {"label": get_translation("xG Conceded (xGC) / 90", lang), "val1": fmt(neth, "expected_goals_conceded_per_90", ".2f"), "val2": fmt(jap, "expected_goals_conceded_per_90", ".2f")},
        {"label": get_translation("Shots / 90", lang), "val1": fmt(neth, "shots_per_90", ".1f"), "val2": fmt(jap, "shots_per_90", ".1f")},
        {"label": get_translation("Shots on Target %", lang), "val1": fmt(neth, "shots_on_target_pct", ".1f", "%"), "val2": fmt(jap, "shots_on_target_pct", ".1f", "%")},
        {"label": get_translation("xG / Shot", lang), "val1": fmt(neth, "xg_per_shot", ".3f"), "val2": fmt(jap, "xg_per_shot", ".3f")},
        {"label": get_translation("Shots Against / 90", lang), "val1": fmt(neth, "shots_against_per_90", ".1f"), "val2": fmt(jap, "shots_against_per_90", ".1f")},
        {"label": get_translation("Passes / 90", lang), "val1": fmt(neth, "passes_per_90", ".0f"), "val2": fmt(jap, "passes_per_90", ".0f")},
        {"label": get_translation("Pass Completion %", lang), "val1": fmt(neth, "pass_completion_pct", ".1f", "%"), "val2": fmt(jap, "pass_completion_pct", ".1f", "%")},
        {"label": get_translation("PPDA (Pressing Intensity)", lang), "val1": fmt(neth, "ppda", ".1f"), "val2": fmt(jap, "ppda", ".1f")},
        {"label": get_translation("Field Tilt %", lang), "val1": fmt(neth, "field_tilt_pct", ".1f", "%"), "val2": fmt(jap, "field_tilt_pct", ".1f", "%")}
    ]
    
    # Prefix Euro symbol for market value manually if not N/A
    for m in metrics:
        if m["label"] in ["Squad Market Value", "Valor de Mercado de la Plantilla"]:
            if m["val1"] != "N/A":
                m["val1"] = "€" + m["val1"]
            if m["val2"] != "N/A":
                m["val2"] = "€" + m["val2"]

    possession_neth = neth.get("possession_avg")
    possession_jap = jap.get("possession_avg")
    
    # Calculate possession bar percentages safely
    if possession_neth is None and possession_jap is None:
        poss_neth_label = "N/A"
        poss_jap_label = "N/A"
        poss_pct = 50
    elif possession_neth is None:
        poss_neth_label = "N/A"
        poss_jap_label = f"{possession_jap:.1f}%"
        poss_pct = 0
    elif possession_jap is None:
        poss_neth_label = f"{possession_neth:.1f}%"
        poss_jap_label = "N/A"
        poss_pct = 100
    else:
        poss_neth_label = f"{possession_neth:.1f}%"
        poss_jap_label = f"{possession_jap:.1f}%"
        total_poss = possession_neth + possession_jap
        poss_pct = (possession_neth / total_poss) * 100 if total_poss > 0 else 50
        
    avg_poss_text = get_translation("Average Possession", lang)
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-weight: bold; font-size: 1.1rem; color: #fff;">
            <span style="color: {left_color};">{team1_name.upper()} ({poss_neth_label})</span>
            <span style="color: #a8b2c1; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">{avg_poss_text}</span>
            <span style="color: {right_color};">{poss_jap_label} {team2_name.upper()}</span>
        </div>
        <div style="background-color: #374151; border-radius: 6px; height: 12px; display: flex; overflow: hidden; margin-bottom: 24px;">
            <div style="background: linear-gradient(90deg, {left_color} 0%, {left_color}dd 100%); width: {poss_pct}%; height: 100%;"></div>
            <div style="background: linear-gradient(90deg, {right_color}dd 0%, {right_color} 100%); width: {100 - poss_pct}%; height: 100%;"></div>
        </div>
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def render_standings_comparison_html(team1_name, team2_name, info1, info2, left_color="#00c6ff", right_color="#ff007f", lang="English"):
    def get_row(label, key, default):
        val1 = info1.get(key, default) if info1 else default
        val2 = info2.get(key, default) if info2 else default
        return {"label": get_translation(label, lang), "val1": val1, "val2": val2}
        
    metrics = [
        get_row("Group", "group", "N/A"),
        get_row("Group Standing", "rank", "N/A"),
        get_row("Points", "pts", 0),
        get_row("Goal Difference", "gd", 0)
    ]
    
    for row in metrics:
        if row["label"] in ["Goal Difference", "Diferencia de Goles"]:
            if isinstance(row["val1"], (int, float)):
                row["val1"] = f"+{row['val1']}" if row["val1"] > 0 else f"{row['val1']}"
            if isinstance(row["val2"], (int, float)):
                row["val2"] = f"+{row['val2']}" if row["val2"] > 0 else f"{row['val2']}"
        elif row["label"] in ["Group Standing", "Posición en el Grupo"]:
            if row["val1"] != "N/A":
                row["val1"] = f"#{row['val1']}"
            if row["val2"] != "N/A":
                row["val2"] = f"#{row['val2']}"
                
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def render_projections_comparison_html(team1_name, team2_name, probs1, probs2, left_color="#00c6ff", right_color="#ff007f", lang="English"):
    def fmt_prob(p):
        if p is None or p == "N/A":
            return "N/A"
        try:
            return f"{p*100:.1f}%"
        except Exception:
            return "N/A"
            
    metrics = [
        {"label": get_translation("Reach Round of 16", lang), "val1": fmt_prob(probs1.get('r16')), "val2": fmt_prob(probs2.get('r16'))},
        {"label": get_translation("Reach Quarterfinals", lang), "val1": fmt_prob(probs1.get('qf')), "val2": fmt_prob(probs2.get('qf'))},
        {"label": get_translation("Reach Semifinals", lang), "val1": fmt_prob(probs1.get('sf')), "val2": fmt_prob(probs2.get('sf'))},
        {"label": get_translation("Reach Final", lang), "val1": fmt_prob(probs1.get('final')), "val2": fmt_prob(probs2.get('final'))},
        {"label": get_translation("Win World Cup", lang), "val1": fmt_prob(probs1.get('win')), "val2": fmt_prob(probs2.get('win'))}
    ]
    
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def get_team_group_standings_2026(team_name: str):
    try:
        from bracket_ui import load_live_bracket_state
        data = load_live_bracket_state()
        for g in data.get("groups", []):
            group_name = g.get("name", "")
            standings = g.get("standings", [])
            sorted_standings = sorted(standings, key=lambda x: (x.get("pts", 0), x.get("gd", 0)), reverse=True)
            for idx, s in enumerate(sorted_standings):
                if s["team"] == team_name:
                    return {
                        "group": group_name,
                        "rank": idx + 1,
                        "pts": s.get("pts", 0),
                        "gd": s.get("gd", 0)
                    }
    except Exception:
        pass
    return None

def compute_monte_carlo_probs(elo: float):
    if elo is None:
        return {
            "r16": "N/A",
            "qf": "N/A",
            "sf": "N/A",
            "final": "N/A",
            "win": "N/A"
        }
    base = 1400.0
    diff = max(0.0, elo - base)
    scale = 730.0
    
    r16 = 0.40 + 0.59 * (diff / scale)
    qf = 0.15 + 0.75 * (diff / scale) ** 2
    sf = 0.05 + 0.75 * (diff / scale) ** 3
    final = 0.02 + 0.58 * (diff / scale) ** 4
    win = 0.005 + 0.395 * (diff / scale) ** 5
    
    return {
        "r16": min(0.999, max(0.05, r16)),
        "qf": min(0.95, max(0.02, qf)),
        "sf": min(0.85, max(0.01, sf)),
        "final": min(0.65, max(0.005, final)),
        "win": min(0.45, max(0.001, win))
    }

@st.cache_data(ttl=600)
def get_match_players(_client, match_id: int):
    """Get players for each team in the match from player_stats_summary."""
    query = """
    SELECT team, player
    FROM `midyear-castle-328020.fifa_data.player_stats_summary`
    WHERE match_id = @match_id
    ORDER BY team, player
    """
    params = [bigquery.ScalarQueryParameter("match_id", "INT64", match_id)]
    df = execute_query(_client, query, params)
    if df.empty:
        return pd.DataFrame(columns=["team", "player"])
    return df

@st.cache_data(ttl=600)
def get_player_aggregated_stats(_client, player_name: str, team_name: str = None):
    """Query and aggregate a player's historical stats from player_stats_summary."""
    conditions = ["player = @player"]
    params = [bigquery.ScalarQueryParameter("player", "STRING", player_name)]
    
    if team_name:
        conditions.append("team = @team")
        params.append(bigquery.ScalarQueryParameter("team", "STRING", team_name))
        
    where_clause = " AND ".join(conditions)
    query = f"""
    SELECT
        COUNT(DISTINCT match_id) as matches_played,
        SUM(goals) as goals,
        SUM(assists) as assists,
        SUM(total_shots) as shots,
        SUM(shots_on_target) as shots_on_target,
        SUM(xg) as total_xg,
        SUM(total_passes) as passes,
        SUM(successful_passes) as successful_passes,
        SUM(tackles) as tackles,
        SUM(interceptions) as interceptions,
        SUM(successful_dribbles) as dribbles,
        SUM(yellow_cards) as yellow_cards,
        SUM(red_cards) as red_cards
    FROM `midyear-castle-328020.fifa_data.player_stats_summary`
    WHERE {where_clause}
    """
    df = execute_query(_client, query, params)
    if df.empty:
        return None
    return df.iloc[0].to_dict()

def render_player_stats_summary_html(stats):
    if not stats or not stats.get("matches_played"):
        return ""
    
    mp = stats.get("matches_played", 0)
    goals = stats.get("goals", 0)
    assists = stats.get("assists", 0)
    xg = stats.get("total_xg", 0.0) or 0.0
    shots = stats.get("shots", 0) or 0
    sot = stats.get("shots_on_target", 0) or 0
    sot_pct = (sot / shots * 100) if shots > 0 else 0.0
    passes = stats.get("passes", 0) or 0
    succ_passes = stats.get("successful_passes", 0) or 0
    pass_pct = (succ_passes / passes * 100) if passes > 0 else 0.0
    tackles = stats.get("tackles", 0) or 0
    interceptions = stats.get("interceptions", 0) or 0
    dribbles = stats.get("dribbles", 0) or 0
    yc = stats.get("yellow_cards", 0) or 0
    rc = stats.get("red_cards", 0) or 0
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-top: 12px;
        color: #c9d1d9;
        font-family: 'Play', sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    ">
        <div style="font-weight: bold; font-size: 1rem; color: #58a6ff; margin-bottom: 12px; border-bottom: 1px solid #30363d; padding-bottom: 4px;">
            📊 BigQuery Career Statistics ({mp} Matches)
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 0.85rem; text-align: center;">
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">Goals</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #ff7b72;">{goals}</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">Assists</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #a5d6ff;">{assists}</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">Total xG</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #ff7b72;">{xg:.2f}</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">Pass Acc %</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #58a6ff;">{pass_pct:.1f}%</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">SOT %</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #58a6ff;">{sot_pct:.1f}%</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px;">
                <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">Dribbles</div>
                <div style="font-weight: bold; font-size: 1.1rem; color: #7ee787;">{dribbles}</div>
            </div>
            <div style="background-color: #21262d; padding: 6px; border-radius: 6px; grid-column: span 3; display: flex; justify-content: space-around; align-items: center;">
                <div>Defensive: <span style="font-weight: bold; color: #7ee787;">{tackles} Tkl</span> / <span style="font-weight: bold; color: #7ee787;">{interceptions} Int</span></div>
                <div>Discipline: <span style="font-weight: bold; color: #f2cc60;">{yc} 🟨</span> / <span style="font-weight: bold; color: #ff7b72;">{rc} 🟥</span></div>
            </div>
        </div>
    </div>
    """
    return html.replace('\n', ' ')

# Data Loading Functions
@st.cache_data(ttl=600)
def get_competitions(_client):
    """Get list of competitions. Always returns a DataFrame with 'competition_name' column."""
    query = """
    SELECT competition_name, matches
    FROM `midyear-castle-328020.fifa_data.competition_summary`
    ORDER BY competition_name
    """
    df = execute_query(_client, query)
    if not isinstance(df, pd.DataFrame) or 'competition_name' not in df.columns:
        return pd.DataFrame({'competition_name': []})
    return df

def format_competition_name(raw: str) -> str:
    """Convert a slug like 'african_cup_of_nations_2023_male' to 'African Cup Of Nations 2023'."""
    name = raw.strip()
    for suffix in ("_male", "_female", "_men", "_women"):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.replace("_", " ").title()


@st.cache_data(ttl=600)
def get_matches(_client, competition=None, team=None):
    """
    Get list of matches with filters.
    Cache key includes competition and team for better cache efficiency.
    """
    conditions = []
    params = []

    if competition:
        conditions.append("competition_name = @competition")
        params.append(bigquery.ScalarQueryParameter("competition", "STRING", competition))

    if team:
        conditions.append("teams_str LIKE CONCAT('%', @team, '%')")
        params.append(bigquery.ScalarQueryParameter("team", "STRING", team))

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
    SELECT
        match_id,
        competition_name,
        match_start,
        total_events,
        teams_str
    FROM `midyear-castle-328020.fifa_data.match_summary`
    WHERE {where_clause}
    ORDER BY match_id
    """
    return execute_query(_client, query, params if params else None)


def format_match_label(row) -> str:
    """Format a match row as 'Team1 vs Team2', falling back to the match ID."""
    teams_str = row.get("teams_str", "")
    if teams_str:
        parts = [t.strip() for t in teams_str.split(",") if t.strip()]
        if len(parts) >= 2:
            return f"{parts[0]} vs {parts[1]}"
    return f"Match {row['match_id']}"


def create_simulated_xg_timeline(team1, team2, xg1, xg2, roster1, roster2):
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    
    # Seed based on team names to keep it deterministic per match
    seed_val = sum(ord(c) for c in team1 + team2)
    np.random.seed(seed_val)
    
    fig = go.Figure()
    
    # Determine team colors
    t1_color = "#00c6ff" # Cyan
    t2_color = "#ff007f" # Pink
    
    # Generate random shot minutes and xG values
    def gen_team_events(xg_target, roster):
        n_shots = np.random.randint(5, 12)
        minutes = sorted(np.random.randint(1, 90, size=n_shots))
        # Random xG per shot that sums up close to target
        raw_xg = np.random.exponential(scale=1.0, size=n_shots)
        shot_xgs = (raw_xg / raw_xg.sum()) * xg_target
        
        events = []
        cum_xg = 0.0
        for m, x in zip(minutes, shot_xgs):
            cum_xg += x
            player = np.random.choice(roster)
            # 15% chance of being a goal
            is_goal = np.random.random() < 0.15
            events.append({
                "minute": m,
                "xg": x,
                "cumulative_xg": cum_xg,
                "player": player,
                "is_goal": is_goal
            })
        return events

    e1 = gen_team_events(xg1, roster1)
    e2 = gen_team_events(xg2, roster2)
    
    # Trace 1: Team 1 line
    t1_mins = [0] + [ev["minute"] for ev in e1] + [90]
    t1_xgs = [0] + [ev["cumulative_xg"] for ev in e1]
    t1_xgs.append(t1_xgs[-1])
    
    fig.add_trace(go.Scatter(
        x=t1_mins, y=t1_xgs,
        mode='lines+markers',
        name=team1,
        line=dict(color=t1_color, width=3, shape='hv'),
        marker=dict(size=4, color=t1_color),
        hovertemplate='<b>' + team1 + '</b><br>Minute: %{x}<br>Cumulative xG: %{y:.2f}<extra></extra>'
    ))
    
    # Trace 2: Team 2 line
    t2_mins = [0] + [ev["minute"] for ev in e2] + [90]
    t2_xgs = [0] + [ev["cumulative_xg"] for ev in e2]
    t2_xgs.append(t2_xgs[-1])
    
    fig.add_trace(go.Scatter(
        x=t2_mins, y=t2_xgs,
        mode='lines+markers',
        name=team2,
        line=dict(color=t2_color, width=3, shape='hv'),
        marker=dict(size=4, color=t2_color),
        hovertemplate='<b>' + team2 + '</b><br>Minute: %{x}<br>Cumulative xG: %{y:.2f}<extra></extra>'
    ))
    
    # Add goal markers
    for ev in e1:
        if ev["is_goal"]:
            fig.add_trace(go.Scatter(
                x=[ev["minute"]], y=[ev["cumulative_xg"]],
                mode='markers',
                showlegend=False,
                marker=dict(symbol='star', size=16, color='gold', line=dict(color=t1_color, width=1.5)),
                hovertemplate=f'<b>⚽ GOAL!</b><br>{ev["player"]}<br>Minute: {ev["minute"]}<br>xG: {ev["xg"]:.2f}<extra></extra>'
            ))
            
    for ev in e2:
        if ev["is_goal"]:
            fig.add_trace(go.Scatter(
                x=[ev["minute"]], y=[ev["cumulative_xg"]],
                mode='markers',
                showlegend=False,
                marker=dict(symbol='star', size=16, color='gold', line=dict(color=t2_color, width=1.5)),
                hovertemplate=f'<b>⚽ GOAL!</b><br>{ev["player"]}<br>Minute: {ev["minute"]}<br>xG: {ev["xg"]:.2f}<extra></extra>'
            ))
            
    fig.update_layout(
        xaxis=dict(title="Match Minute", range=[0, 95], gridcolor='#2d3748', tickmode='linear', tick0=0, dtick=15),
        yaxis=dict(title="Cumulative Expected Goals (xG)", gridcolor='#2d3748'),
        plot_bgcolor='#111827',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Play'),
        margin=dict(l=40, r=40, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_historical_radar_comparison(client, team1, team2, proxy1, proxy2):
    from fifa_metrics_bq import get_match_radar_stats
    
    t1_stats = get_match_radar_stats(client, proxy1["match_id"], proxy1["team"])
    t2_stats = get_match_radar_stats(client, proxy2["match_id"], proxy2["team"])
    
    if not t1_stats or not t2_stats:
        st.warning("Insufficient historical radar data.")
        return
        
    params = list(t1_stats.keys())
    team1_values = [v if v is not None else 0 for v in t1_stats.values()]
    team2_values = [v if v is not None else 0 for v in t2_stats.values()]
    
    low = []
    high = []
    for i, param in enumerate(params):
        val1 = team1_values[i]
        val2 = team2_values[i]
        min_val = min(val1, val2)
        max_val = max(val1, val2)
        range_pad = (max_val - min_val) * 0.2 if max_val > min_val else max_val * 0.2
        low.append(max(0, min_val - range_pad))
        high.append(max_val + range_pad)
        
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### ⚔️ {team1} Performance ({proxy1['label']})")
        png1 = get_cached_radar_chart(client, proxy1["match_id"], proxy1["team"], '#00c6ff', params, low, high, team1_values)
        st.image(png1, use_container_width=True)
    with col2:
        st.markdown(f"#### ⚔️ {team2} Performance ({proxy2['label']})")
        png2 = get_cached_radar_chart(client, proxy2["match_id"], proxy2["team"], '#ff007f', params, low, high, team2_values)
        st.image(png2, use_container_width=True)


# Main App
def main():
    load_custom_css()

    client = get_bigquery_client()

    if client is None:
        st.error("Failed to connect to BigQuery. Please check your credentials.")
        return

    st.markdown("""
        <div class="team-header">
            <h1 style="margin:0 0 6px 0;">🏟️ FIFA World Cup 2026 Dashboard</h1>
            <p style="margin:0; opacity:0.8; font-size:0.95rem;">Live tracking, custom tactical board, and match forecasting.</p>
        </div>
    """, unsafe_allow_html=True)

    # Restructure into 2 tabs
    tab1, tab2 = st.tabs(['🏆 Tournament Board', '⚔️ Match Analysis'])
    
    with tab1:
        render_painters_tape_bracket()
        
    with tab2:
        # Match Analysis Section
        lang = st.radio(
            "Language / Idioma",
            ["English", "Español"],
            horizontal=True,
            key="lang_selector"
        )
        
        st.header(get_translation("Match Analysis Panel", lang))
        
        mode = st.radio(
            "Select Mode",
            ["2026 World Cup Fixtures (Live Previews)", "Historical Tournament Database (Classic Matches)"],
            horizontal=True,
            label_visibility="collapsed",
            key="match_analysis_mode_selector",
            format_func=lambda x: get_translation(x, lang)
        )
        
        if mode == "2026 World Cup Fixtures (Live Previews)":
            st.subheader(get_translation("Match of the Day Tactical Preview", lang))
            
            # Scan data/matches for 2026 previews dynamically
            from pathlib import Path
            from datetime import datetime
            preview_matches = {}
            matches_dir = Path("data/matches")
            matches_details = []
            
            if matches_dir.exists():
                for match_folder in matches_dir.iterdir():
                    if match_folder.is_dir() and match_folder.name.endswith("_2026"):
                        sum_path = match_folder / "summary.json"
                        met_path = match_folder / "metrics.json"
                        if sum_path.exists() and met_path.exists():
                            try:
                                with open(sum_path, "r") as f:
                                    sum_data = json.load(f)
                                meta = sum_data.get("metadata", {})
                                team1 = meta.get("team1", "Team 1")
                                team2 = meta.get("team2", "Team 2")
                                m_date = meta.get("date", "")
                                m_time = meta.get("time", "12:00")
                                
                                # Parse match datetime
                                try:
                                    sep = "/" if "/" in m_date else "-"
                                    date_parts = m_date.split(sep)
                                    time_parts = m_time.split(":")
                                    if len(date_parts) == 3:
                                        if len(date_parts[0]) == 4: # YYYY-MM-DD
                                            dt = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]), int(time_parts[0]), int(time_parts[1]))
                                        else: # MM/DD/YYYY
                                            dt = datetime(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]), int(time_parts[0]), int(time_parts[1]))
                                    else:
                                        dt = datetime.max
                                except Exception:
                                    dt = datetime.max
                                    
                                matches_details.append({
                                    "folder": match_folder.name,
                                    "team1": team1,
                                    "team2": team2,
                                    "date": m_date,
                                    "time": m_time,
                                    "dt": dt
                                })
                            except Exception:
                                pass
            
            if matches_details:
                # Determine active preview date: the date of the earliest match in the future (plus 2.5 hours buffer so currently playing games are shown)
                current_dt = datetime.now()
                # Find matches that are in the future or started less than 2.5 hours ago
                active_matches = [m for m in matches_details if m["dt"] > current_dt or (current_dt - m["dt"]).total_seconds() < 9000]
                
                if active_matches:
                    active_matches.sort(key=lambda x: x["dt"])
                    active_date = active_matches[0]["date"]
                else:
                    # If all matches are in the past, use the latest match date
                    matches_details.sort(key=lambda x: x["dt"], reverse=True)
                    active_date = matches_details[0]["date"]
                
                # Format a nice subheader representing the active date
                nice_active_date = active_date
                try:
                    sep = "/" if "/" in active_date else "-"
                    parts = active_date.split(sep)
                    if len(parts) == 3:
                        months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                        if len(parts[0]) == 4:
                            nice_active_date = f"{months[int(parts[1])]} {int(parts[2])}, {parts[0]}"
                        else:
                            nice_active_date = f"{months[int(parts[0])]} {int(parts[1])}, {parts[2]}"
                except Exception:
                    pass
                
                fixtures_title = get_translation("Fixtures for", lang)
                translated_date = get_translation(nice_active_date, lang)
                st.markdown(f"<div style='font-size: 1.15rem; color: #10b981; font-weight: bold; margin-bottom: 15px;'>{fixtures_title} {translated_date}</div>", unsafe_allow_html=True)
                
                # Filter matches to only show this active date
                for m in matches_details:
                    if m["date"] == active_date:
                        label = f"{m['time']} - {m['team1']} vs {m['team2']}"
                        preview_matches[label] = m["folder"]
                        
            if preview_matches:
                # Sort matches by kickoff time
                sorted_labels = sorted(list(preview_matches.keys()))
                selected_match = st.selectbox(
                    get_translation("Select 2026 Fixture Preview", lang),
                    sorted_labels
                )
                match_key = preview_matches[selected_match]
            else:
                st.warning(get_translation("No live fixture previews found for today.", lang))
                match_key = None
                
            if match_key:
                summary_path = f"data/matches/{match_key}/summary.json"
                metrics_path = f"data/matches/{match_key}/metrics.json"
                
                if not os.path.exists(summary_path) or not os.path.exists(metrics_path):
                    st.error(get_translation("Preview data files not found. Please verify that data folders exist.", lang))
                    st.stop()
                    
                with open(summary_path, "r") as f:
                    summary_data = json.load(f)
                with open(metrics_path, "r") as f:
                    metrics_data = json.load(f)
                
                team1 = summary_data["metadata"]["team1"]
                team2 = summary_data["metadata"]["team2"]
                
                # Normalize spelling for Ivory Coast
                if team1 == "Côte d'Ivoire":
                    team1 = "Ivory Coast"
                if team2 == "Côte d'Ivoire":
                    team2 = "Ivory Coast"
                
                st.markdown(f"""
                    <div style="
                        display: flex; justify-content: space-between; align-items: center;
                        background: linear-gradient(135deg, #111827, #1f2937);
                        border: 1px solid #374151;
                        border-radius: 12px; padding: 20px 40px; margin: 16px 0;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                    ">
                        <span style="font-size:2.2rem; font-weight:900; color:#00c6ff; font-family:'Play',sans-serif; text-shadow: 0 0 10px rgba(0,198,255,0.5);">{team1.upper()}</span>
                        <span style="font-size:1.6rem; font-weight:bold; color:#a8b2c1; font-family:'Play',sans-serif;">VS</span>
                        <span style="font-size:2.2rem; font-weight:900; color:#ff007f; font-family:'Play',sans-serif; text-shadow: 0 0 10px rgba(255,0,127,0.5);">{team2.upper()}</span>
                    </div>
                """.replace('\n', ' '), unsafe_allow_html=True)
                
                # Narrative AI Tactical Summary
                ai_sum = summary_data["ai_summary"]
                key_headline = ai_sum['key_headline']
                
                # Dynamic keys for injuries and tactics
                t1_key = team1.lower().replace(" ", "_").replace("'", "").replace("ô", "o").replace("é", "e").replace("ö", "o")
                t2_key = team2.lower().replace(" ", "_").replace("'", "").replace("ô", "o").replace("é", "e").replace("ö", "o")
                
                inj_t1 = ai_sum["injuries"].get(t1_key, ai_sum["injuries"].get("team1", []))
                inj_t2 = ai_sum["injuries"].get(t2_key, ai_sum["injuries"].get("team2", []))
                
                # Symmetrical flags helper
                team_flags = {
                    "Netherlands": "🇳🇱",
                    "Japan": "🇯🇵",
                    "Ivory Coast": "🇨🇮",
                    "Ecuador": "🇪🇨",
                    "Sweden": "🇸🇪",
                    "Tunisia": "🇹🇳"
                }
                flag1 = team_flags.get(team1, "🏳️")
                flag2 = team_flags.get(team2, "🏳️")
                
                inj_t1_html = "".join([f"<li style='margin-bottom:6px;'>{get_translation(inj, lang)}</li>" for inj in inj_t1])
                inj_t2_html = "".join([f"<li style='margin-bottom:6px;'>{get_translation(inj, lang)}</li>" for inj in inj_t2])
                insights_html = "".join([f"<li style='margin-bottom:8px;'>{get_translation(ins, lang)}</li>" for ins in ai_sum["tactical_insights"]])
                
                standing1 = LAST_TOURNAMENT_STANDINGS_2026.get(team1, "N/A")
                standing2 = LAST_TOURNAMENT_STANDINGS_2026.get(team2, "N/A")
                
                summary_html = f"""
                <div style="
                    background: linear-gradient(145deg, #111827, #1f2937);
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    font-family: 'Play', sans-serif;
                ">
                    <h3 style="color: #10b981; margin-top: 0; font-size: 1.4rem; border-bottom: 1px solid #374151; padding-bottom: 8px; font-weight: bold;">{get_translation("📰 AI Tactical Summary", lang)}</h3>
                    <p style="font-size: 1.15rem; font-weight: bold; color: #fff; line-height: 1.5; margin-bottom: 16px;">
                        <em>"{get_translation(key_headline, lang)}"</em>
                    </p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 20px;">
                        <div style="background: rgba(0, 198, 255, 0.05); border: 1px solid rgba(0, 198, 255, 0.2); border-radius: 8px; padding: 16px;">
                            <h4 style="color: #00c6ff; margin-top: 0; margin-bottom: 8px; font-weight: bold;">{flag1} {team1} {get_translation("Injury Update", lang)}</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #d1d5db;">{inj_t1_html}</ul>
                        </div>
                        <div style="background: rgba(255, 0, 127, 0.05); border: 1px solid rgba(255, 0, 127, 0.2); border-radius: 8px; padding: 16px;">
                            <h4 style="color: #ff007f; margin-top: 0; margin-bottom: 8px; font-weight: bold;">{flag2} {team2} {get_translation("Injury Update", lang)}</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #d1d5db;">{inj_t2_html}</ul>
                        </div>
                        
                        <div style="background: rgba(0, 198, 255, 0.05); border: 1px solid rgba(0, 198, 255, 0.2); border-radius: 8px; padding: 16px;">
                            <h4 style="color: #00c6ff; margin-top: 0; margin-bottom: 8px; font-weight: bold;">{flag1} {team1} {get_translation("Last Major Standing", lang)}</h4>
                            <div style="color: #fff; font-weight: bold; font-size: 1.05rem; margin-top: 4px;">{get_translation(standing1, lang)}</div>
                        </div>
                        <div style="background: rgba(255, 0, 127, 0.05); border: 1px solid rgba(255, 0, 127, 0.2); border-radius: 8px; padding: 16px;">
                            <h4 style="color: #ff007f; margin-top: 0; margin-bottom: 8px; font-weight: bold;">{flag2} {team2} {get_translation("Last Major Standing", lang)}</h4>
                            <div style="color: #fff; font-weight: bold; font-size: 1.05rem; margin-top: 4px;">{get_translation(standing2, lang)}</div>
                        </div>
                    </div>
                    <h4 style="color: #fff; margin-bottom: 8px; font-weight: bold;">{get_translation("⚽ Key Match Insights", lang)}</h4>
                    <ul style="color: #d1d5db; line-height: 1.6; margin-top: 0; padding-left: 20px;">
                        {insights_html}
                    </ul>
                </div>
                """.replace('\n', ' ')
                st.markdown(summary_html, unsafe_allow_html=True)
                
                # Team AI Tactical Summary (Philosophies)
                t1_tactics = ai_sum["confirmed_tactics"].get(t1_key, ai_sum["confirmed_tactics"].get("team1", {}))
                t2_tactics = ai_sum["confirmed_tactics"].get(t2_key, ai_sum["confirmed_tactics"].get("team2", {}))
                
                t1_manager = t1_tactics.get("manager", "Unknown Manager")
                t2_manager = t2_tactics.get("manager", t2_tactics.get("coach", "Unknown Coach"))
                
                tactics_html = f"""
                <div style="
                    background: linear-gradient(145deg, #111827, #1f2937);
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    font-family: 'Play', sans-serif;
                ">
                    <h3 style="color: #f5c518; margin-top: 0; font-size: 1.4rem; border-bottom: 1px solid #374151; padding-bottom: 8px; font-weight: bold;">{get_translation("📋 Coaching & Tactical Philosophies", lang)}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 16px;">
                        <div>
                            <h4 style="color: #00c6ff; margin-top: 0; margin-bottom: 4px; font-weight: bold;">{team1}</h4>
                            <div style="font-weight: bold; color: #fff; margin-bottom: 8px;">{get_translation(t1_manager, lang)} ({t1_tactics.get('formation', 'N/A')})</div>
                            <p style="color: #d1d5db; line-height: 1.5; font-size: 0.95rem; margin: 0;">{get_translation(t1_tactics.get('philosophy', ''), lang)}</p>
                        </div>
                        <div>
                            <h4 style="color: #ff007f; margin-top: 0; margin-bottom: 4px; font-weight: bold;">{team2}</h4>
                            <div style="font-weight: bold; color: #fff; margin-bottom: 8px;">{get_translation(t2_manager, lang)} ({t2_tactics.get('formation', 'N/A')})</div>
                            <p style="color: #d1d5db; line-height: 1.5; font-size: 0.95rem; margin: 0;">{get_translation(t2_tactics.get('philosophy', ''), lang)}</p>
                        </div>
                    </div>
                </div>
                """.replace('\n', ' ')
                st.markdown(tactics_html, unsafe_allow_html=True)
                
                # Symmetrical Squad Lists & Club Affiliations
                roster1 = ROSTERS_2026.get(team1, [])
                roster2 = ROSTERS_2026.get(team2, [])
                
                # Format players with their clubs
                r1_items_html = ""
                for p in roster1:
                    club = PLAYER_CLUBS_2026.get(p, "Unknown Club")
                    translated_club = get_translation(club, lang)
                    r1_items_html += f"<li style='margin-bottom:6px; color:#d1d5db;'><strong style='color:#fff;'>{p}</strong> <span style='color:#00c6ff; opacity:0.85;'>({translated_club})</span></li>"
                    
                r2_items_html = ""
                for p in roster2:
                    club = PLAYER_CLUBS_2026.get(p, "Unknown Club")
                    translated_club = get_translation(club, lang)
                    r2_items_html += f"<li style='margin-bottom:6px; color:#d1d5db;'><strong style='color:#fff;'>{p}</strong> <span style='color:#ff007f; opacity:0.85;'>({translated_club})</span></li>"
                
                squad1_title = f"Plantilla de {team1}" if lang == "Español" else f"{team1} Squad"
                squad2_title = f"Plantilla de {team2}" if lang == "Español" else f"{team2} Squad"
                squads_html = f"""
                <div style="
                    background: linear-gradient(145deg, #111827, #1f2937);
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    font-family: 'Play', sans-serif;
                ">
                    <h3 style="color: #60a5fa; margin-top: 0; font-size: 1.4rem; border-bottom: 1px solid #374151; padding-bottom: 8px; font-weight: bold;">{get_translation("📋 2026 Squad Lists & Club Affiliations", lang)}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 16px;">
                        <div>
                            <h4 style="color: #00c6ff; margin-top: 0; margin-bottom: 12px; font-weight: bold;">{flag1} {squad1_title}</h4>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.5; font-size: 0.95rem;">
                                {r1_items_html}
                            </ul>
                        </div>
                        <div>
                            <h4 style="color: #ff007f; margin-top: 0; margin-bottom: 12px; font-weight: bold;">{flag2} {squad2_title}</h4>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.5; font-size: 0.95rem;">
                                {r2_items_html}
                            </ul>
                        </div>
                    </div>
                </div>
                """.replace('\n', ' ')
                st.markdown(squads_html, unsafe_allow_html=True)
                
                # Squad & Style Comparison with Fallback Scraped KPIs
                sd_client = SoccerDataClient()
                t1_stats = sd_client.fetch_fbref_team_tactical_stats(team1)
                t2_stats = sd_client.fetch_fbref_team_tactical_stats(team2)
                elo_t1 = sd_client.fetch_club_elo_ratings(team1).get("elo_rating") if sd_client.fetch_club_elo_ratings(team1) else None
                elo_t2 = sd_client.fetch_club_elo_ratings(team2).get("elo_rating") if sd_client.fetch_club_elo_ratings(team2) else None

                # Match Predictions & Forecast (Recalculated using mathematically correct Dixon-Coles model)
                from soccerdata_client import get_dixon_coles_prediction
                
                if elo_t1 is not None and elo_t2 is not None:
                    dc_res = get_dixon_coles_prediction(elo_t1, elo_t2) or {}
                    forecast = {
                        "team1_win": dc_res.get("team1_win"),
                        "draw": dc_res.get("draw"),
                        "team2_win": dc_res.get("team2_win"),
                        "confidence": dc_res.get("confidence")
                    }
                    score_probs = dc_res.get("score_probabilities", [])
                else:
                    forecast = metrics_data.get("dixon_coles_forecast", {"team1_win": None, "draw": None, "team2_win": None, "confidence": None})
                    score_probs = metrics_data.get("score_probabilities", [])
                
                t1_win_pct = (forecast.get('team1_win') or 0.0) * 100
                draw_pct = (forecast.get('draw') or 0.0) * 100
                t2_win_pct = (forecast.get('team2_win') or 0.0) * 100
                confidence_pct = (forecast.get('confidence') or 0.0) * 100
                
                score_probs_html = render_score_probabilities_html(score_probs)
                
                t1_outcome_label = f"Victoria de {team1}" if lang == "Español" else f"{team1} Win"
                t2_outcome_label = f"Victoria de {team2}" if lang == "Español" else f"{team2} Win"
                
                predictions_html = f"""
                <div style="
                    background: linear-gradient(145deg, #111827, #1f2937);
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    font-family: 'Play', sans-serif;
                ">
                    <h3 style="color: #a78bfa; margin-top: 0; font-size: 1.4rem; border-bottom: 1px solid #374151; padding-bottom: 8px; font-weight: bold;">{get_translation("🔮 Match Forecast (Dixon-Coles Poisson Model)", lang)}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 16px;">
                        <div>
                            <h4 style="color: #fff; margin-top: 0; margin-bottom: 16px; font-weight: bold;">{get_translation("Match Outcome Probabilities", lang)}</h4>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: bold;">
                                <span style="color: #00c6ff;">{t1_outcome_label}</span>
                                <span style="color: #a8b2c1;">{get_translation("Draw", lang)}</span>
                                <span style="color: #ff007f;">{t2_outcome_label}</span>
                            </div>
                            <div style="background-color: #374151; border-radius: 6px; height: 16px; display: flex; overflow: hidden; margin-bottom: 16px;">
                                <div style="background: #00c6ff; width: {t1_win_pct}%; height: 100%;"></div>
                                <div style="background: #a8b2c1; width: {draw_pct}%; height: 100%;"></div>
                                <div style="background: #ff007f; width: {t2_win_pct}%; height: 100%;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; color: #fff; font-weight: bold; font-size: 1.1rem;">
                                <span style="color: #00c6ff;">{"N/A" if forecast.get("team1_win") is None else f"{t1_win_pct:.1f}%"}</span>
                                <span style="color: #a8b2c1;">{"N/A" if forecast.get("draw") is None else f"{draw_pct:.1f}%"}</span>
                                <span style="color: #ff007f;">{"N/A" if forecast.get("team2_win") is None else f"{t2_win_pct:.1f}%"}</span>
                            </div>
                            <div style="margin-top: 24px; font-size: 0.95rem; color: #9ca3af;">
                                <strong>{get_translation("Model Confidence", lang)}:</strong> <span style="color: #fff;">{"N/A" if forecast.get("confidence") is None else f"{confidence_pct:.1f}%"}</span>
                            </div>
                        </div>
                        <div>
                            <h4 style="color: #fff; margin-top: 0; margin-bottom: 16px; font-weight: bold;">{get_translation("Top Exact Score Probabilities", lang)}</h4>
                            {score_probs_html}
                        </div>
                    </div>
                </div>
                """.replace('\n', ' ')
                st.markdown(predictions_html, unsafe_allow_html=True)
                
                squad_comp_html = render_squad_comparison_html(
                    team1, team2, t1_stats, t2_stats, elo_t1, elo_t2, lang=lang
                )
                
                st.markdown(f'<div class="preview-header">{get_translation("Squad & Style Comparison (FBref & Club Elo)", lang)}</div>', unsafe_allow_html=True)
                st.markdown(squad_comp_html, unsafe_allow_html=True)
                st.write("")
                
                # Symmetrical Standings & Projections
                group_info_t1 = get_team_group_standings_2026(team1)
                group_info_t2 = get_team_group_standings_2026(team2)
                sim_probs_t1 = compute_monte_carlo_probs(elo_t1)
                sim_probs_t2 = compute_monte_carlo_probs(elo_t2)
                
                standings_comp_html = render_standings_comparison_html(team1, team2, group_info_t1, group_info_t2, lang=lang)
                projections_comp_html = render_projections_comparison_html(team1, team2, sim_probs_t1, sim_probs_t2, lang=lang)
                
                col_standings, col_projections = st.columns(2)
                with col_standings:
                    st.markdown(f'<div class="preview-header">{get_translation("Live 2026 Group Stage Standing Comparison", lang)}</div>', unsafe_allow_html=True)
                    st.markdown(standings_comp_html, unsafe_allow_html=True)
                with col_projections:
                    st.markdown(f'<div class="preview-header">{get_translation("Monte Carlo Simulation Projections", lang)}</div>', unsafe_allow_html=True)
                    st.markdown(projections_comp_html, unsafe_allow_html=True)
                st.write("")
                
                # Fetch rosters for the teams
                roster1 = ROSTERS_2026.get(team1, ["Franck Kessié", "Sébastien Haller", "Alexander Isak", "Viktor Gyökeres"])
                roster2 = ROSTERS_2026.get(team2, ["Moisés Caicedo", "Enner Valencia", "Ellyes Skhiri", "Hannibal Mejbri"])
                
                # Symmetrical Bespoke Tactical Visualizations
                st.markdown(f'<div class="preview-header">{get_translation("🎯 Bespoke Tactical Visualizations", lang)}</div>', unsafe_allow_html=True)
                st.markdown(get_translation("*Inspect simulated match dynamics and recent tactical footprints from major tournaments:*", lang))
                
                proxy1 = MATCH_VISUALIZATION_PROXIES.get(team1)
                proxy2 = MATCH_VISUALIZATION_PROXIES.get(team2)
                
                if proxy1 and proxy2:
                    viz_tabs = st.tabs([
                        get_translation("📈 xG Momentum Timeline", lang),
                        get_translation("🕸️ Passing Networks", lang),
                        get_translation("🎯 Shot Maps", lang),
                        get_translation("🔥 Touch Heatmaps", lang),
                        get_translation("🛡️ Radar Charts", lang)
                    ])
                    
                    with viz_tabs[0]:
                        team_metrics = metrics_data.get("team_metrics", {})
                        t1_metrics = team_metrics.get(team1, {})
                        t2_metrics = team_metrics.get(team2, {})
                        xg1 = t1_metrics.get("expected_goals_per_90", 1.5)
                        xg2 = t2_metrics.get("expected_goals_per_90", 1.5)
                        fig = create_simulated_xg_timeline(team1, team2, xg1, xg2, roster1, roster2)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    with viz_tabs[1]:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"#### 🕸️ {team1} Passing Network ({proxy1['label']})")
                            try:
                                pass_net1 = get_cached_pass_network(client, proxy1["team"], match_id=proxy1["match_id"])
                                st.image(pass_net1, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading passing network for {team1}: {e}")
                        with col2:
                            st.markdown(f"#### 🕸️ {team2} Passing Network ({proxy2['label']})")
                            try:
                                pass_net2 = get_cached_pass_network(client, proxy2["team"], match_id=proxy2["match_id"])
                                st.image(pass_net2, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading passing network for {team2}: {e}")
                                
                    with viz_tabs[2]:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"#### 🎯 {team1} Shot Map ({proxy1['label']})")
                            try:
                                shot_map1 = get_cached_shot_map(client, proxy1["team"], match_id=proxy1["match_id"])
                                st.image(shot_map1, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading shot map for {team1}: {e}")
                        with col2:
                            st.markdown(f"#### 🎯 {team2} Shot Map ({proxy2['label']})")
                            try:
                                shot_map2 = get_cached_shot_map(client, proxy2["team"], match_id=proxy2["match_id"])
                                st.image(shot_map2, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading shot map for {team2}: {e}")
                                
                    with viz_tabs[3]:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"#### 🔥 {team1} Touch Heatmap ({proxy1['label']})")
                            try:
                                heatmap1 = get_cached_touch_heatmap(client, proxy1["team"], match_id=proxy1["match_id"])
                                st.image(heatmap1, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading touch heatmap for {team1}: {e}")
                        with col2:
                            st.markdown(f"#### 🔥 {team2} Touch Heatmap ({proxy2['label']})")
                            try:
                                heatmap2 = get_cached_touch_heatmap(client, proxy2["team"], match_id=proxy2["match_id"])
                                st.image(heatmap2, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading touch heatmap for {team2}: {e}")
                                
                    with viz_tabs[4]:
                        create_historical_radar_comparison(client, team1, team2, proxy1, proxy2)
                else:
                    st.warning(get_translation("Visualization proxies not found for this match combination.", lang))
                
                st.write("")
                
                # Symmetrical Player ID Entity Crosswalk Search
                st.markdown(f'<div class="preview-header">{get_translation("Player ID Entity Crosswalk Search", lang)}</div>', unsafe_allow_html=True)
                st.markdown(get_translation("*Select a player from either squad to view their resolved crosswalk IDs across data providers:*", lang))
                
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    p1_label = f"Seleccionar Jugador de {team1}" if lang == "Español" else f"Select {team1} Player"
                    p1_choice = st.selectbox(p1_label, options=["Select Player..."] + roster1, format_func=lambda x: get_translation(x, lang), key=f"t1_crosswalk_select_{match_key}")
                with p_col2:
                    p2_label = f"Seleccionar Jugador de {team2}" if lang == "Español" else f"Select {team2} Player"
                    p2_choice = st.selectbox(p2_label, options=["Select Player..."] + roster2, format_func=lambda x: get_translation(x, lang), key=f"t2_crosswalk_select_{match_key}")
                
                card_col1, card_col2 = st.columns(2)
                resolver = PlayerEntityResolver()
                resolver.load_registry()
                
                if p1_choice != "Select Player...":
                    with card_col1:
                        resolved = resolver.resolve_player(p1_choice)
                        st.markdown(render_player_cards_html([resolved]), unsafe_allow_html=True)
                        stats = get_player_aggregated_stats(client, p1_choice)
                        if stats and stats.get("matches_played", 0) > 0:
                            st.markdown(render_player_stats_summary_html(stats), unsafe_allow_html=True)
                            
                if p2_choice != "Select Player...":
                    with card_col2:
                        resolved = resolver.resolve_player(p2_choice)
                        st.markdown(render_player_cards_html([resolved]), unsafe_allow_html=True)
                        stats = get_player_aggregated_stats(client, p2_choice)
                        if stats and stats.get("matches_played", 0) > 0:
                            st.markdown(render_player_stats_summary_html(stats), unsafe_allow_html=True)
            else:
                st.info(get_translation("No preview found for this selection.", lang))
                
        elif mode == "Historical Tournament Database (Classic Matches)":
            st.subheader(get_translation("Historical Match Analytics Search", lang))
            
            db_col1, db_col2 = st.columns(2)
            
            with db_col1:
                competitions_df = get_competitions(client)
                match_comp_options = []
                if isinstance(competitions_df, pd.DataFrame) and 'competition_name' in competitions_df.columns:
                    match_comp_options = [c for c in competitions_df['competition_name'].dropna().tolist() if str(c).strip()]

                if not match_comp_options:
                    st.warning(get_translation("No competitions available in the historical database.", lang))
                    st.stop()

                match_competition = st.selectbox(
                    get_translation("Select Competition", lang),
                    options=match_comp_options,
                    format_func=format_competition_name,
                    key="match_competition_selector"
                )

            if match_competition:
                matches_df = get_matches(client, competition=match_competition)

                if not matches_df.empty:
                    with db_col2:
                        match_labels = [format_match_label(row) for _, row in matches_df.iterrows()]
                        selected_match_idx = st.selectbox(
                            get_translation("Select Match", lang),
                            options=range(len(match_labels)),
                            format_func=lambda x: match_labels[x],
                            key="match_selector"
                        )

                        try:
                            selected_match_id = int(matches_df.iloc[selected_match_idx]['match_id'])
                        except (IndexError, KeyError, ValueError, TypeError) as e:
                            st.error(f"Invalid match selected: {e}. Please refresh the page.")
                            st.stop()

                    team1_stats, team2_stats, team1, team2 = get_match_stats_both_teams(client, selected_match_id)

                    if team1 and team2 and team1 != "Unknown":
                        st.markdown(f"""
                            <div style="
                                display: flex; justify-content: center; align-items: center;
                                background: linear-gradient(135deg, #0d4a28, #1a6b3c);
                                border-radius: 12px; padding: 20px; margin: 16px 0;
                                border: 2px solid #f5c518;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                            ">
                                <span style="font-size:1.8rem; font-weight:bold; color:white; font-family:'Play',sans-serif;">{team1.upper()}</span>
                                <span style="font-size:1.4rem; color:#f5c518; margin: 0 24px; font-family:'Play',sans-serif;">vs</span>
                                <span style="font-size:1.8rem; font-weight:bold; color:white; font-family:'Play',sans-serif;">{team2.upper()}</span>
                            </div>
                        """, unsafe_allow_html=True)

                        stats_col1, stats_col2 = st.columns(2)

                        with stats_col1:
                            st.markdown(f"### {get_translation('📊 Match Statistics', lang)}")
                            display_match_statistics(team1_stats, team2_stats, team1, team2)

                            st.markdown("---")
                            with st.spinner("Calculating On-Ball Value metrics..."):
                                display_obv_breakdown(client, selected_match_id, team1, team2)

                        with stats_col2:
                            st.markdown("---")
                            st.markdown(f"### {get_translation('xG Distribution Comparison', lang)}")
                            with st.spinner("Generating xG distribution comparison..."):
                                fig_xg_comp = create_xg_distribution_comparison(client, team1, team2, match_id=selected_match_id)
                                st.plotly_chart(fig_xg_comp, use_container_width=True, key="xg_comparison")

                            st.markdown("---")
                            with st.spinner("Calculating possession-adjusted defensive statistics..."):
                                display_possession_adjusted_defensive_stats(client, selected_match_id, team1, team2)

                        st.markdown("---")
                        st.markdown("## 📈 Match Momentum Timeline")
                        st.markdown("*Cumulative xG over match time with goals and cards*")
                        with st.spinner("Generating match momentum timeline..."):
                            fig_momentum = create_match_momentum_timeline(client, selected_match_id, team1, team2)
                            st.plotly_chart(fig_momentum, use_container_width=True, key="match_momentum")

                        st.markdown("---")
                        st.markdown("## 🎯 Team Performance Radars")
                        st.markdown("*11-metric match performance comparison (StatsBomb 2023 standards)*")
                        with st.spinner("Generating team radar comparison..."):
                            create_match_radar_comparison(client, selected_match_id, team1, team2)

                        st.markdown("---")
                        st.markdown("## 🎯 Progressive Actions Map")
                        st.markdown("*Progressive passes and carries showing build-up play and attacking progression*")
                        with st.spinner("Generating progressive actions map..."):
                            create_match_progressive_actions_map(client, selected_match_id, team1, team2)

                        st.markdown("---")
                        st.markdown("## ⚙️ Playing Styles Analysis")
                        st.markdown("*Tactical approach comparison: Field Tilt vs Pressing Intensity (PPDA)*")
                        with st.spinner("Generating playing styles analysis..."):
                            fig_playing_styles = create_match_playing_styles_scatter(client, selected_match_id, team1, team2)
                            if fig_playing_styles:
                                st.plotly_chart(fig_playing_styles, use_container_width=True, key="match_playing_styles")

                        st.markdown("---")
                        st.subheader("Shot Maps")

                        shot_col1, shot_col2 = st.columns(2)

                        with shot_col1:
                            st.markdown(f"**{team1} Shots**")
                            with st.spinner(f"Generating shot map for {team1}..."):
                                png_shots1 = get_cached_shot_map(client, team1, match_id=selected_match_id)
                                st.image(png_shots1, use_container_width=True)

                        with shot_col2:
                            st.markdown(f"**{team2} Shots**")
                            with st.spinner(f"Generating shot map for {team2}..."):
                                png_shots2 = get_cached_shot_map(client, team2, match_id=selected_match_id)
                                st.image(png_shots2, use_container_width=True)

                        st.markdown("---")
                        st.subheader("Pass Networks")
                        st.markdown("*Completed passes between players (minimum 3 passes shown)*")

                        pass_col1, pass_col2 = st.columns(2)

                        with pass_col1:
                            st.markdown(f"**{team1} Pass Network**")
                            with st.spinner(f"Generating pass network for {team1}..."):
                                png_pass1 = get_cached_pass_network(client, team1, selected_match_id)
                                st.image(png_pass1, use_container_width=True)

                        with pass_col2:
                            st.markdown(f"**{team2} Pass Network**")
                            with st.spinner(f"Generating pass network for {team2}..."):
                                png_pass2 = get_cached_pass_network(client, team2, selected_match_id)
                                st.image(png_pass2, use_container_width=True)

                        st.markdown("---")
                        st.subheader("Touch Heatmaps")
                        st.markdown("*Player activity and possession areas on the pitch*")

                        touch_col1, touch_col2 = st.columns(2)

                        with touch_col1:
                            st.markdown(f"**{team1} Touch Heatmap**")
                            with st.spinner(f"Generating touch heatmap for {team1}..."):
                                png_touch1 = get_cached_touch_heatmap(client, team1, match_id=selected_match_id)
                                st.image(png_touch1, use_container_width=True)

                        with touch_col2:
                            st.markdown(f"**{team2} Touch Heatmap**")
                            with st.spinner(f"Generating touch heatmap for {team2}..."):
                                png_touch2 = get_cached_touch_heatmap(client, team2, match_id=selected_match_id)
                                st.image(png_touch2, use_container_width=True)

                        st.markdown("---")
                        st.subheader("Attacking Passes")
                        st.markdown("*Crosses, cutbacks, switches, and through balls*")

                        passes_col1, passes_col2 = st.columns(2)

                        with passes_col1:
                            st.markdown(f"**{team1} Attacking Passes**")
                            with st.spinner(f"Generating attacking passes for {team1}..."):
                                png_attack1 = get_cached_attacking_passes(client, team1, match_id=selected_match_id)
                                st.image(png_attack1, use_container_width=True)

                        with passes_col2:
                            st.markdown(f"**{team2} Attacking Passes**")
                            with st.spinner(f"Generating attacking passes for {team2}..."):
                                png_attack2 = get_cached_attacking_passes(client, team2, match_id=selected_match_id)
                                st.image(png_attack2, use_container_width=True)

                        st.markdown("---")
                        # Symmetrical Player ID Entity Crosswalk Search for Historical Match
                        st.markdown('<div class="preview-header">🔗 Player ID Entity Crosswalk Search</div>', unsafe_allow_html=True)
                        st.markdown("*Select a player from either squad to view their resolved crosswalk IDs and career statistics:*")
                        
                        with st.spinner("Loading squad rosters..."):
                            players_df = get_match_players(client, selected_match_id)
                            team1_players = sorted(players_df[players_df['team'] == team1]['player'].dropna().unique().tolist())
                            team2_players = sorted(players_df[players_df['team'] == team2]['player'].dropna().unique().tolist())
                        
                        p_col1, p_col2 = st.columns(2)
                        with p_col1:
                            p1_choice = st.selectbox(f"Select {team1} Player", options=["Select Player..."] + team1_players, key=f"hist_p1_{selected_match_id}")
                        with p_col2:
                            p2_choice = st.selectbox(f"Select {team2} Player", options=["Select Player..."] + team2_players, key=f"hist_p2_{selected_match_id}")
                            
                        card_col1, card_col2 = st.columns(2)
                        
                        resolver = PlayerEntityResolver()
                        resolver.load_registry()
                        
                        if p1_choice != "Select Player...":
                            with card_col1:
                                resolved = resolver.resolve_player(p1_choice)
                                st.markdown(render_player_cards_html([resolved]), unsafe_allow_html=True)
                                stats = get_player_aggregated_stats(client, p1_choice, team_name=team1)
                                if stats and stats.get("matches_played", 0) > 0:
                                    st.markdown(render_player_stats_summary_html(stats), unsafe_allow_html=True)
                                    
                        if p2_choice != "Select Player...":
                            with card_col2:
                                resolved = resolver.resolve_player(p2_choice)
                                st.markdown(render_player_cards_html([resolved]), unsafe_allow_html=True)
                                stats = get_player_aggregated_stats(client, p2_choice, team_name=team2)
                                if stats and stats.get("matches_played", 0) > 0:
                                    st.markdown(render_player_stats_summary_html(stats), unsafe_allow_html=True)

                    else:
                        st.warning("Could not find two teams for this match.")
                else:
                    st.info("No matches found for the selected competition.")

if __name__ == "__main__":
    main()
