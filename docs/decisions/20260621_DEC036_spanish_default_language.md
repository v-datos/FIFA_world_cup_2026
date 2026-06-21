# DEC036 - Spanish as Default Dashboard Language

Date: 2026-06-21

## Status

Accepted.

## Context

The tournament dashboard initially loaded with English as the default language. Given that the main target audience and the primary operational context benefit from a Spanish interface, the default language should be set to Spanish (`Español`) on load, while retaining full functionality of the language selector to switch back to English.

## Decision

- **Default State Modification**: Modified `src/frontend/src/App.tsx` to set the initial value of the `lang` React state to `'Español'` instead of `'English'`.
- **Language Selector Integrity**: Ensured that the EN/ES toggle selector in the sidebar remains fully functional, allowing users to toggle between Spanish and English seamlessly.

## Consequences

- The analytics dashboard loads all tabs, headlines, key insights, and lineup tactical philosophies in Spanish by default on initial page load.
- Seamless toggling to English remains available via the language switcher in the sidebar.
