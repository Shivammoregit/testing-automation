# Frontend/version-manager (App Version Manager)

## Role
Express + MongoDB service with a static UI to track app versions for ios and android in production and development.

## Tech stack
- Node.js + Express
- MongoDB (native driver)
- Static HTML and JS UI

## Entry points
- server/index.js (API + static)
- public/app.js (UI logic)

## API
- POST /api/auth (passkey)
- GET /api/health
- GET, POST, PUT, DELETE /api/releases
- GET /api/releases/filter/breaking

## Config and env
- MONGODB_URI
- PORT

## Environment URLs
- Prod: `https://versions.petyosa.com`
- Dev: `https://versions.petyosa.com`

## Interconnections
- Intended to support mobile release workflows (seed data includes ios-parent, android-parent, ios-partner, android-partner).

## Health, testing
- /api/health endpoint
- Seeds default passkey "admin123" on first run (server/index.js)
- No test scripts configured
