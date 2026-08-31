# Naval AI — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS dashboard for the
Naval Vessel Detection & Classification backend.

## Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # point at your backend
npm run dev
```

Visit `http://localhost:3000`.

## Pages

- `/` — landing page
- `/dashboard` — fleet-wide stats and recent uploads chart
- `/upload` — drag-and-drop image/video upload with live detection results
- `/history` — full detection history, with delete + report download
- `/reports` — report-focused card view for downloading PDFs
- `/settings` — backend connection status and config file pointers
- `/about` — project overview, ship classes, tech stack

## Design system

Dark navy/steel-blue "tactical console" theme (tokens in `app/globals.css`).
Signature element: bracket-cornered panels (`.bracket-panel`, wrapped by
`components/BracketPanel.tsx`) — a targeting-reticle motif fitting a
detection system, used everywhere instead of plain cards. Fonts: Rajdhani
(display/headers), Inter (body), JetBrains Mono (data — confidence scores,
timestamps, track IDs).

Hazard colors (`safe`/`suspicious`/`hazardous`/`unknown`) are defined once
in `globals.css` and intentionally match `backend/config/hazard_rules.yaml`
and `backend/reports/generator.py`'s PDF styling, so the color of "hazardous"
means the same thing everywhere in the system.
