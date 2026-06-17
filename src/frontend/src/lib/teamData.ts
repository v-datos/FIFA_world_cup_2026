// Shared team metadata: national flags + the current tournament date.
// Single source of truth used across the Overview and Match Analysis tabs.

export const TEAM_FLAGS: Record<string, string> = {
  "Argentina": "🇦🇷", "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
  "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Canada": "🇨🇦", "Qatar": "🇶🇦",
  "Czechia": "🇨🇿", "Czech Republic": "🇨🇿", "South Africa": "🇿🇦", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "Croatia": "🇭🇷", "France": "🇫🇷", "Senegal": "🇸🇳", "Ghana": "🇬🇭",
  "Panama": "🇵🇦", "Iran": "🇮🇷", "New Zealand": "🇳🇿", "Iraq": "🇮🇶",
  "Norway": "🇳🇴", "Mexico": "🇲🇽", "South Korea": "🇰🇷", "Portugal": "🇵🇹",
  "DR Congo": "🇨🇩", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾", "Spain": "🇪🇸",
  "Cape Verde": "🇨🇻", "Switzerland": "🇨🇭", "Bosnia and Herzegovina": "🇧🇦",
  "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  "United States": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Turkiye": "🇹🇷",
  "Turkey": "🇹🇷", "Germany": "🇩🇪", "Curacao": "🇨🇼", "Ivory Coast": "🇨🇮",
  "Ecuador": "🇪🇨", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
  "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴", "Bosnia": "🇧🇦"
};

export const getFlag = (team: string): string => TEAM_FLAGS[team] || "🏳️";

// Each team's most recent major-tournament finish (curated).
export const LAST_MAJOR_STANDING: Record<string, string> = {
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
  "Argentina": "Champions (FIFA World Cup 2022 & Copa América 2024)",
  "Algeria": "Group Stage (Africa Cup of Nations 2023)",
  "Austria": "Round of 16 (UEFA Euro 2024)",
  "Jordan": "Runners-up (AFC Asian Cup 2023)",
};

export const getLastStanding = (team: string): string | null => LAST_MAJOR_STANDING[team] || null;

// Current active tournament date (MM/DD/YYYY) used to filter "games of the day".
export const TODAY_DATE = "06/16/2026";
