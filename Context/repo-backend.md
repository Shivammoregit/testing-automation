# Backend (Core API)

## Role
Primary API and realtime backend for the platform: user onboarding, pets, vet operations, grooming, hostel, marketplace, community chat, admin workflows, analytics, payments, and integrations.

## Tech stack
- Node.js + Express
- MongoDB (Mongoose), Redis, Elasticsearch
- Socket.IO realtime layer
- GCP: Pub/Sub, Cloud Tasks, Storage
- Firebase Admin, Agora, Razorpay
- OpenAI and Dialogflow CX
- Joi and Zod validation
- Winston and Morgan logging

## Entry points
- src/index.js (server bootstrap and Socket.IO)
- src/app.js (Express app and route registration)

## Structure
- src/controllers/ (domain logic)
- src/models/ (Mongoose schemas)
- src/routes/v1/ (REST modules)
- src/sockets/ (realtime)
- src/utils/ (integrations)
- src/validations/ (Joi schemas)
- docs/ (admin API references)

## Health, observability, testing
- Health endpoint: GET /api/v1/info/health (src/routes/v1/info.js)
- Logging: src/config/logger.js and src/config/morgan.js
- Jest config present (jest.config.js) and Supertest dependency
- Dockerfile, cloudbuild.yaml, and PM2 ecosystem.config.json for deployment

## Interconnections
- Frontend apps call /api/v1 for REST and Socket.IO for realtime.
- Auth service calls Backend token endpoint (BACKEND_API).
- DigiLocker integration: calls digiBAckend for KYC (DIGI_BACKEND, DIGILOCKER_PUBLIC_URL) and syncs data into vet and hostel onboarding.
- External services: GCP, Firebase, Agora, Razorpay, OpenAI, Dialogflow, MSG91, FCM, etc.

## Notable flows
- Vet and hostel onboarding use DigiLocker KYC via src/controllers/vetController.js and src/controllers/hostelController.js.
- Realtime chat via src/sockets/index.js with JWT auth.
