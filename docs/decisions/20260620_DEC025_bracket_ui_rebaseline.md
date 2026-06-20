# DEC025 - Standings & Bracket Tab UI Rebaseline (Streamlit Wood Board Alignment)

Date: 2026-06-20  
Authority: Orchestrator / Frontend Engineer  
Status: Accepted  

## Context

The React client's Standings tab (`StandingsTab.tsx`) was migrated to display group standings and the tournament bracket tree. However, the visual appearance drifted from the legacy Streamlit `bracket_ui.py` layout, which utilized a meticulously tuned CSS layout simulating individual, slightly-rotated painter's tape strips placed on a wood board panel. The current React version has straight, rigid cards with scores on matchup tapes, leading to text wrapping and a cluttered look that drifts from the original premium and clean aesthetic.

## Decision

Rebaseline `StandingsTab.tsx` to match the legacy Streamlit bracket board system:

1. **Board Aesthetics**: Revert the wood board background color to `#c1925a` (wood color) and restore the original radial-gradient and repeating-linear-gradient properties (spaced at `20px` intervals).
2. **Organic Rotations**: Re-introduce individual inline CSS rotations to the group teams box (`-0.5deg`) and each group standings strip (P, W, D, L, GD, Pts) using the index-based even/odd rotation formula.
3. **Clean Matchups**: Remove match score badges from the team tapes in the matchup cells (Round of 32 through Semifinals, Final, and Third Place) to match the clean presentation of the legacy application and prevent layout overflows.
4. **Proportion & Spacing**: Match the exact heights and widths of columns:
   - Left/Right Group height: `920px`, width: `280px`
   - Left/Right Bracket height: `920px`, width: `480px`
   - Round column width: `105px`
   - Center column height: `920px`, width: `130px`
   - Team tape width: `90px` (final match: `105px`, third place: `80px`)
   - Bracket vertical connector heights: R32 = `59px`, R16 = `117px`, QF = `233px`

## Rationale

- **Aesthetic Fidelity**: The wood board panel and slightly crooked painter's tape strips were a major highlight of the original dashboard's design. Rigid layout grids make the React port look like a generic dashboard, violating the premium visual excellence rule.
- **Data Density**: Hiding scores from the bracket tapes keeps the layout clean. Users can already check exact scores and match details in the Overview or Match Analysis tabs; the bracket serves as a high-level visual progress map.

## Consequences

- The bracket tree will look identical to the original Streamlit application.
- Columns will fit viewports cleanly with horizontal scrolling enabled for viewports below `1720px`.
- Verification requires compiling the client and checking the visual alignment in the browser.
