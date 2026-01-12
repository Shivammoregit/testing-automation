# Frontend/responsive-simulator

## Role
Internal tool to test a URL across many device sizes and capture accept or reject results.

## Tech stack
- Vite + React 18 + TypeScript
- shadcn-ui + Tailwind CSS
- Tanstack Query, Sonner toasts

## Entry points
- src/main.tsx (Vite entry)
- src/pages/Index.tsx (simulator)
- src/data/devices.ts (device list)

## Features
- Load a URL into simulated device frames
- Auto or manual advance across devices
- Accept or reject with CSV export of results

## Interconnections
- No backend calls; runs fully client side

## Health, testing
- ESLint configured
- No test scripts configured
