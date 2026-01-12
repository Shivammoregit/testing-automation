# Frontend/pet-admin (Admin Portal)

## Role
Admin UI for vet onboarding, PetBNB host management, reviews, analytics, and operations.

## Tech stack
- Vite + React 18 + TypeScript
- Tailwind CSS + shadcn-ui + Radix UI
- Tanstack Query, Axios, Zod, Zustand

## Entry points
- src/main.tsx, src/App.tsx
- src/lib/axios.ts (API clients)
- src/constants/env.ts (env)

## Config and env
- VITE_BACKEND_URL
- VITE_AUTHENTICATION_URL
- Firebase, Agora, Razorpay, Maps keys (optional)

## Environment URLs
- Prod: app `https://admin.petyosa.com`, backend `https://backend.petyosa.com`, auth `https://auth.petyosa.com`
- Dev: app `https://devadmin.petyosa.com`, backend `https://devbackend.petyosa.com`, auth `https://devauth.petyosa.com`

## Interconnections
- Backend admin endpoints under /api/v1/admin/*
- Hostel management endpoints under /api/v1/admin/hostel-management

## Health, testing
- ESLint configured (npm run lint)
- No test scripts configured

## Notes
- Several API modules include mocked data and TODO notes for backend integration (src/lib/api/admin.ts).
