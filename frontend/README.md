# KyberChat Frontend

React (Vite) frontend for the KyberChat secure communication platform.

## Setup
```bash
npm install
cp .env.example .env      # set VITE_BACKEND_URL to your running Flask backend
npm run dev                # http://localhost:5173
```

## Build
```bash
npm run build               # outputs to dist/
```

## Structure
- `src/api/client.js` — single fetch wrapper for every backend endpoint
- `src/context/AuthContext.jsx` — session state
- `src/components/` — Sidebar, Layout, MessageComposer (AI enhance UI), route guards
- `src/pages/` — one file per screen (Login, Chats, GroupChats, Files, AI Enhancer,
  Simulation, Performance, Health, Admin*, Profile, Team Members)

## Design
Plain CSS with design tokens in `src/styles/index.css` — no Tailwind/UI kit dependency,
Inter typeface, restrained neutral palette with a single accent color, per the project's
UI/UX requirements (no gradients, neon, or glassmorphism).
