# Frontend/partner (Partner App)

## Role
Vet and partner SPA for onboarding, scheduling, consultations, and analytics.

## Tech stack
- React 19 (Create React App)
- Redux Toolkit + Redux Persist
- React Router 7
- MUI, Bootstrap, custom CSS
- Agora RTC, Firebase, Socket.IO client
- Maps: Google Maps, Leaflet

## Entry points
- src/App.js, src/Routes.js
- src/host.js (API host config)

## Config and env
- REACT_APP_BACKEND_URL (core API)
- REACT_APP_AUTHENTICATION_URL (OTP service)
- Firebase, Agora, VAPID, Maps keys
Defined in src/host.js.

## Environment URLs
- Prod: app `https://partnerapp.petyosa.com`, backend `https://backend.petyosa.com`, auth `https://auth.petyosa.com`
- Dev: app `https://devpartnerapp.petyosa.com`, backend `https://devbackend.petyosa.com`, auth `https://devauth.petyosa.com`

## Interconnections
- Backend REST and sockets
- Auth service for OTP
- Firebase and Agora external services

## Mobile builds
- Capacitor dependencies included in package.json
- Native wrappers under Frontend/partner/android and Frontend/partner/ios

## Health, testing, deployment
- CRA build pipeline; Dockerfile + cloudbuild.yaml
- package.json has dev and build scripts; no explicit test script
