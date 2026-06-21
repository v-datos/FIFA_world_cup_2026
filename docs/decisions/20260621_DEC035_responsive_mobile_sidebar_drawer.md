# DEC035 - Responsive Mobile Sidebar Drawer

Date: 2026-06-21

## Status

Accepted.

## Context

The analytics dashboard featured a sidebar navigation layout designed for desktop. On mobile and tablet screens, the sidebar remained permanently visible on the left side of the screen, leaving very little horizontal space for the main dashboard tabs. This made the layout extremely squished and unusable on smaller viewports.

To optimize the dashboard for phones and tablets, the sidebar needed to be responsive, hiding on smaller viewports by default and toggling into view as a sliding overlay drawer when requested.

## Decision

- **Mobile Header**: Added a sticky mobile top bar (`md:hidden`) at the top of the viewport containing a logo, title, and a hamburger menu button.
- **Drawer Behavior for Sidebar**: Updated `components/Sidebar.tsx` to transition between:
  - **Desktop (md and up)**: Sticky side panel, always visible, collapses horizontally.
  - **Mobile/Tablet**: Fixed-drawer container. Slides in/out from the left side of the screen (`translate-x-0` vs `-translate-x-full`) with a dark, blurred backdrop overlay (`z-35`).
- **Drawer Close Action**: Included a close button (`X` icon) at the top of the mobile drawer and wired it to close the drawer automatically when clicking the backdrop overlay or switching navigation tabs.
- **Dynamic Padding**: Adjusted main content panel padding (`p-4` on mobile, `md:p-8` on desktop) to optimize space.

## Consequences

- Full mobile and tablet responsiveness across the entire dashboard interface.
- Sidebar collapses and slides out cleanly on phone screens, matching standard mobile application patterns.
- Content containers (such as grids and charts) flow to the full viewport width on mobile, optimizing data readability.
