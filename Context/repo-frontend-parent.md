# Frontend/parent (Parent App)

## Role
User facing web app for pet owners: discovery, booking, community, chat, and payments.

## Tech stack
- React 19 (Create React App)
- Redux Toolkit + Redux Persist
- React Router 7
- MUI v6, Bootstrap, custom CSS
- Socket.IO client
- Firebase (auth + FCM)
- Agora for video calls
- Razorpay for payments
- Maps: Google Maps, Leaflet

## Entry points
- src/App.js, src/Routes.js
- src/host.js (API host config)
- public/firebase-messaging-sw.js (FCM service worker)

## Structure
- src/pages/ (feature screens)
- src/components/ (UI)
- src/actions/, src/reducers/, src/store.js (Redux)
- src/contexts/ (Socket context)
- src/assets/ (CSS, images)

## Config and env
- REACT_APP_BACKEND_URL (core API)
- REACT_APP_AUTHENTICATION_URL (OTP service)
- REACT_APP_DIGILOCKER_URL (KYC service)
- Firebase, Agora, Razorpay, Maps keys
Defined in src/host.js.

## Environment URLs
- Prod: app `https://app.petyosa.com`, backend `https://backend.petyosa.com`, auth `https://auth.petyosa.com`, DigiLocker `https://devdigibackend.petyosa.com`
- Dev: app `https://devapp.petyosa.com`, backend `https://devbackend.petyosa.com`, auth `https://devauth.petyosa.com`, DigiLocker `https://devdigibackend.petyosa.com`

## Interconnections
- Backend REST and sockets
- Auth service for OTP
- DigiLocker backend for KYC onboarding
- Firebase and Agora external services

## Mobile builds
- Capacitor dependency included in package.json
- Separate native wrapper at Frontend/parent-android (Android build)

## Health, testing, deployment
- CRA build pipeline; Dockerfile + cloudbuild.yaml + nginx.conf
- package.json has dev and build scripts; no explicit test script
