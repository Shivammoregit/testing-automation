# Frontend/parent-onboard (Onboarding MFE)

## Role
Onboarding micro frontend embedded by parent and partner apps. It uses postMessage for JWT exchange with the host app.

## Tech stack
- Vite + React 18 + TypeScript
- Tailwind CSS + shadcn-ui
- Axios for API client

## Entry points
- src/main.tsx (BrowserRouter basename /onboard)
- src/App.tsx

## Auth and token bridge
- src/utils/authHandler.ts listens for postMessage (AUTH_TOKEN, REFRESH_TOKEN).
- src/utils/apiClient.ts attaches JWT and requests refresh on 401.

## Config and env
- VITE_BACKEND_API_URL (API base)
- VITE_FRONTEND_API_URL (allowed origin)

## Environment URLs
- Prod: backend `https://backend.petyosa.com/api/v1`, parent app `https://app.petyosa.com`, MFE `https://app.petyosa.com/onboard`
- Dev: backend `https://devbackend.petyosa.com/api/v1`, parent app `https://devapp.petyosa.com`, MFE `https://devapp.petyosa.com/onboard`

## Interconnections
- Backend API for onboarding endpoints
- Parent app for token handshake (postMessage)

## Health, testing
- ESLint configured
- No test scripts configured
