# Auth (OTP Microservice)

## Role
OTP gateway for phone based auth. It sends and verifies OTP via MSG91 or Twilio, then exchanges verified OTP for tokens from the Backend service.

## Tech stack
- Node.js + Express 5
- TypeScript
- Zod validations
- Axios + request-ip
- SMS providers: MSG91, Twilio
- Redis backed rate limiting (ioredis, rate-limit-redis)

## Entry points
- src/server.ts (bootstraps HTTP server)
- src/app.ts (Express setup and routing)

## Structure
- src/routes/auth.routes.ts (check, create, verify)
- src/routes/health.routes.ts (health)
- src/controllers/auth.controller.ts
- src/handlers/ (provider specific logic)
- src/validations/ (Zod schemas)
- src/constants/env.ts (env validation)

## Key endpoints
- POST /api/v1/auth/:service/check
- POST /api/v1/auth/:service/create
- POST /api/v1/auth/:service/verify
- GET /api/v1/health

## Config and env
- BACKEND_API (token exchange URL)
- MSG91_* and TWILIO_* provider settings
- PET_FRONTEND_CORS, VET_FRONTEND_CORS (CORS allowlists)
Defined in src/constants/env.ts.

## Environment URLs
- Service base: prod `https://auth.petyosa.com`, dev `https://devauth.petyosa.com`

## Interconnections
- Calls Backend token endpoint in src/handlers/auth/getTokens.ts.
- Receives requests from parent and partner frontends via REACT_APP_AUTHENTICATION_URL or VITE_AUTHENTICATION_URL.

## Health, observability, testing
- Health endpoint mounted at /api/v1/health.
- Rate limiting middleware in src/middlewares/limiter.middleware.ts.
- No test script configured in package.json.
