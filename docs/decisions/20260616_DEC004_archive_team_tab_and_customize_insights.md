# Decision: Archive Unused Team Tab & Implement Researched Previews & Spanish Translation

Date: 2026-06-16
Authority: Orchestrator
Status: Decided

## Context

1. **Stale Team Tab**: The file `src/app/team_tab.py` is a stale, unused file not integrated into the active Streamlit entrypoint (`src/app/app.py`). It contains duplicate and outdated layouts.
2. **Generic Insights Fallback**: Because Google Vertex AI/Gemini calls failed or were blocked by credentials/billing limits on local and server environments, the automated previews fell back to identical generic Insights ("Both teams will try to establish control...", "Defensive discipline...", "Set-pieces..."), causing a poor user experience.
3. **Spanish Translation Request**: The user requested a clean, toggleable Spanish translation specifically for the Match Analysis tab to allow seamless switching between English and Español for both static UI labels and dynamic AI narratives.

## Ruling

1. **Delete team_tab.py**: Remove the stale `src/app/team_tab.py` from the project directory.
2. **Remove Vertex AI & Curate Match Profiles**: Refactor the preview generator `src/pipeline/generate_match_previews.py` to remove Google Vertex AI generative calls. Replace them with a robust lookup dictionary containing pre-researched, customized tactical profiles (headlines, formations, philosophies, actual injuries, and 3 unique tactical insights) for all 12 scheduled matches.
3. **Implement Spanish Translation on Match Analysis Tab**: Implement a horizontal language selector toggle (`lang_selector`) at the top of the Match Analysis tab inside `src/app/app.py`. Modify comparisons and narrative panels to pass the selected language and dynamically translate UI headers and narrative insights.

## Rationale

- Deleting dead code like `team_tab.py` improves codebase maintainability and prevents confusion.
- Removing unreliable cloud-based Vertex API calls guarantees that match previews will never fail, require zero external API billing/services, and consistently deliver high-quality, pre-researched tactical summaries instead of copy-pasted generic placeholders.
- A toggleable translation helper inside `translation_helper.py` ensures that all custom pre-researched paragraphs and labels transition into natural Spanish when Español is active.

## Implementation Notes

- **Stale Code**: Deleted `src/app/team_tab.py`.
- **Preview Generation**: Updated `src/pipeline/generate_match_previews.py` and regenerated all previews in `data/matches/` with actual curated tactical summaries.
- **Dashboard Translations**: Updated `src/app/app.py` and `src/app/translation_helper.py` to support full translation toggle for the Match Analysis panel.
