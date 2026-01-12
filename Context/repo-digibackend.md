# digiBAckend (DigiLocker KYC Service)

## Role
Handles DigiLocker OAuth (PKCE), collects and normalizes KYC documents, stores them in MongoDB and filesystem, and exposes KYC document retrieval endpoints used by Backend and frontends.

## Tech stack
- Node.js + Express
- MongoDB (Mongoose)
- Axios, qs, xml2js
- Local filesystem storage (STORAGE_ROOT)

## Entry points
- server/index.js (Express and Mongo connection)
- server/routes/digilocker.js (routing)

## Key endpoints
- GET /digilocker/start (OAuth start)
- GET /digilocker/callback (OAuth callback)
- GET /digilocker/session/:id
- GET /digilocker/kyc and /digilocker/kyc/:id
- GET /digilocker/file and /digilocker/file/:kycId/*
- GET /health

## Data models
- server/db/models/pkce.js
- server/db/models/DigiKyc.js
- server/db/models/OnboardingSession.js

## Config and env
- MONGODB_URI
- DL_BASE, DL_CLIENT_ID, DL_CLIENT_SECRET, DL_REDIRECT_URI, DL_SCOPE
- USER_ONBOARDING_URL, VET_ONBOARDING_URL, CORS_ORIGINS
- STORAGE_ROOT (filesystem path)

## Environment URLs
- Service base: prod `https://devdigibackend.petyosa.com`, dev `https://devdigibackend.petyosa.com`

## Interconnections
- Frontend parent app and vet or hostel onboarding flows start OAuth via /digilocker/start.
- Backend calls /digilocker/kyc/:id to sync KYC data.
- External: DigiLocker API, MongoDB, filesystem storage.

## Health, observability, testing
- /health endpoint in server/index.js
- No test runner configured in package.json.
