// Frontend tournament metadata. Team identity and primary flags come from
// teamIdentity.ts; TEAM_FLAGS remains as a legacy fallback for old labels.
import { getTeamFlag, normalizeTeamName } from './teamIdentity';

export const TEAM_FLAGS: Record<string, string> = {
  "Argentina": "🇦🇷", "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
  "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Canada": "🇨🇦", "Qatar": "🇶🇦",
  "Czechia": "🇨🇿", "Czech Republic": "🇨🇿", "South Africa": "🇿🇦", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "Croatia": "🇭🇷", "France": "🇫🇷", "Senegal": "🇸🇳", "Ghana": "🇬🇭",
  "Panama": "🇵🇦", "Iran": "🇮🇷", "New Zealand": "🇳🇿", "Iraq": "🇮🇶",
  "Norway": "🇳🇴", "Mexico": "🇲🇽", "South Korea": "🇰🇷", "Portugal": "🇵🇹",
  "DR Congo": "🇨🇩", "Democratic Republic of the Congo": "🇨🇩", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾", "Spain": "🇪🇸",
  "Cape Verde": "🇨🇻", "Switzerland": "🇨🇭", "Bosnia and Herzegovina": "🇧🇦",
  "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  "United States": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Turkiye": "🇹🇷",
  "Turkey": "🇹🇷", "Germany": "🇩🇪", "Curacao": "🇨🇼", "Ivory Coast": "🇨🇮",
  "Ecuador": "🇪🇨", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
  "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴", "Bosnia": "🇧🇦"
};

export const getFlag = (team: string): string => getTeamFlag(team) || TEAM_FLAGS[team] || "🏳️";

// Each team's most recent major-tournament finish (curated).
export const LAST_MAJOR_STANDING: Record<string, string> = {
  "Netherlands": "Semi-finals (UEFA Euro 2024)",
  "Japan": "Quarter-finals (AFC Asian Cup 2023)",
  "Ivory Coast": "Quarter-finals (Africa Cup of Nations 2025)",
  "Ecuador": "Quarter-finals (Copa América 2024)",
  "Sweden": "Round of 16 (UEFA Euro 2020)",
  "Tunisia": "Round of 16 (Africa Cup of Nations 2025)",
  "Spain": "Champions (UEFA Euro 2024)",
  "Cape Verde": "Did not qualify (Africa Cup of Nations 2025)",
  "Belgium": "Round of 16 (UEFA Euro 2024)",
  "Egypt": "Fourth Place (Africa Cup of Nations 2025)",
  "Saudi Arabia": "Round of 16 (AFC Asian Cup 2023)",
  "Uruguay": "Third Place (Copa América 2024)",
  "Iran": "Semi-finals (AFC Asian Cup 2023)",
  "New Zealand": "Champions (OFC Nations Cup 2024)",
  "France": "Runners-up (FIFA World Cup 2022)",
  "Senegal": "Runners-up (Africa Cup of Nations 2025)",
  "Iraq": "Round of 16 (AFC Asian Cup 2023)",
  "Norway": "Group Stage (UEFA Nations League A 2024)",
  "Argentina": "Champions (FIFA World Cup 2022 & Copa América 2024)",
  "Algeria": "Quarter-finals (Africa Cup of Nations 2025)",
  "Austria": "Round of 16 (UEFA Euro 2024)",
  "Jordan": "Runners-up (AFC Asian Cup 2023)",
  "Morocco": "Champions (Africa Cup of Nations 2025)",
  "Democratic Republic of the Congo": "Round of 16 (Africa Cup of Nations 2025)",
  "DR Congo": "Round of 16 (Africa Cup of Nations 2025)",
  "South Africa": "Round of 16 (Africa Cup of Nations 2025)",
  "Portugal": "Quarter-finals (UEFA Euro 2024)",
  "Colombia": "Runners-up (Copa América 2024)",
  "Mexico": "Champions (CONCACAF Gold Cup 2025)",
  "Croatia": "Group Stage (UEFA Euro 2024)",
  "Ghana": "Did not qualify (Africa Cup of Nations 2025)",
  "South Korea": "Semi-finals (AFC Asian Cup 2023)",
  "Czech Republic": "Group Stage (UEFA Euro 2024)",
  "Czechia": "Group Stage (UEFA Euro 2024)",
  "Canada": "Fourth Place (Copa América 2024)",
  "Bosnia and Herzegovina": "Did not qualify (UEFA Euro 2024)",
  "Bosnia": "Did not qualify (UEFA Euro 2024)",
  "Qatar": "Champions (AFC Asian Cup 2023)",
  "Switzerland": "Quarter-finals (UEFA Euro 2024)",
  "Brazil": "Quarter-finals (Copa América 2024)",
  "Haiti": "Group Stage (CONCACAF Gold Cup 2023)",
  "Scotland": "Group Stage (UEFA Euro 2024)",
  "United States": "Group Stage (Copa América 2024)",
  "Paraguay": "Group Stage (Copa América 2024)",
  "Australia": "Quarter-finals (AFC Asian Cup 2023)",
  "Turkey": "Quarter-finals (UEFA Euro 2024)",
  "Turkiye": "Quarter-finals (UEFA Euro 2024)",
  "Germany": "Quarter-finals (UEFA Euro 2024)",
  "Curacao": "Did not qualify (CONCACAF Gold Cup 2025)",
  "Uzbekistan": "Quarter-finals (AFC Asian Cup 2023)",
  "England": "Runners-up (UEFA Euro 2024)",
  "Panama": "Quarter-finals (Copa América 2024)"
};

export const getLastStanding = (team: string): string | null => (
  LAST_MAJOR_STANDING[normalizeTeamName(team)] || LAST_MAJOR_STANDING[team] || null
);
