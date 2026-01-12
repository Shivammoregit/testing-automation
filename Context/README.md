# Petyosa Context Docs

This folder documents repo roles, structure, tech stack, interconnections, and health signals for the Petyosa codebase.

## Repo map
- Auth: OTP authentication microservice that exchanges verified OTP for Backend tokens.
- Backend: core API, realtime, admin, payments, chat, analytics.
- digiBAckend: DigiLocker OAuth plus KYC store and document retrieval.
- Frontend/parent: parent (pet owner) web app.
- Frontend/partner: partner (vet and clinic) web app.
- Frontend/pet-admin: admin portal (Vite + React).
- Frontend/parent-onboard: onboarding MFE consumed by parent and partner flows.
- Frontend/version-manager: release tracking API and UI.
- Frontend/responsive-simulator: internal UI responsiveness tool.
- Frontend/parent-testing, Frontend/partner-testing: testing clones of the main frontends.
- Jmeter: load test plans and reports.

Other Frontend directories exist (fityosa, groom, onboarding-mfe, pet-homepage, shopyosa, etc) but are not covered here.

## Branching (observed)
User-stated:
- main and prod are production branches
- develop is the latest integration branch
- parent and partner have capacitor and capacitor-ios-dev for mobile builds

Local branch lists observed in these checkouts:
- Auth: develop, deploy/docker (no local main or prod)
- Backend: develop, main, plus feature and fix branches
- digiBAckend: develop, digiandroid (no local main or prod)
- Frontend/parent: develop, main, capacitor, plus feature and fix branches
- Frontend/partner: develop, main, capacitor
- Frontend/pet-admin: develop, feature branches
- Frontend/parent-onboard: main, develop, vite
- Frontend/version-manager: main
- Frontend/responsive-simulator: develop
- Frontend/parent-testing: develop, main, feedapaw, placeholders
- Frontend/partner-testing: develop, capacitor, capacitor-production

Remote branches fetched (not checked out locally):
- Frontend/parent: origin/capacitor-ios-dev, origin/capacitor-production, origin/prod
- Frontend/partner: origin/capacitor-ios-dev, origin/capacitor-ios-ring, origin/prod

## Doc index
- architecture-overview.md
- flowcharts.md
- repo-auth.md
- repo-backend.md
- repo-digibackend.md
- repo-frontend-parent.md
- repo-frontend-partner.md
- repo-frontend-pet-admin.md
- repo-frontend-parent-onboard.md
- repo-version-manager.md
- repo-responsive-simulator.md
- repo-testing.md
