# CogniRoom — Frontend

React 19 + Vite client for the CogniRoom collaborative study room.
See the [root README](../README.md) for the full project overview.

## Setup

```bash
npm install
npm run dev        # http://localhost:5173
```

The dev server expects the backend at `http://localhost:8000`
(configured in `src/api/client.js` and `src/api/socket.js`).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build |
| `npm run lint` | ESLint |

## Structure

```
src/
├── api/          # REST client + Socket.IO service
├── context/      # AuthContext (JWT in localStorage)
├── components/   # Chat, Whiteboard, Quiz, Flashcards, Scheduler, LiveMetrics, AI panel
└── pages/        # Auth, Dashboard, RoomView, Analytics, Mentor/Admin dashboards, Profile
```
