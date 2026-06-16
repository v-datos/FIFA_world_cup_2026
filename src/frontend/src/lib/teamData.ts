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

// Current active tournament date (MM/DD/YYYY) used to filter "games of the day".
export const TODAY_DATE = "06/16/2026";
