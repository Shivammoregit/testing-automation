# Flowcharts

## OTP Auth (Auth service to Backend tokens)
```mermaid
sequenceDiagram
  participant User
  participant Frontend
  participant AuthSvc
  participant SMS
  participant Backend

  User->>Frontend: Enter phone, request OTP
  Frontend->>AuthSvc: POST /api/v1/auth/:service/create
  AuthSvc->>SMS: Send OTP
  SMS-->>User: OTP SMS
  User->>Frontend: Submit OTP
  Frontend->>AuthSvc: POST /api/v1/auth/:service/verify?role=...
  AuthSvc->>Backend: POST BACKEND_API?role=...
  Backend-->>AuthSvc: Access and refresh tokens
  AuthSvc-->>Frontend: Tokens
```

## DigiLocker KYC (digiBAckend)
```mermaid
sequenceDiagram
  participant Frontend
  participant DigiSvc
  participant DigiLocker
  participant Backend

  Frontend->>DigiSvc: GET /digilocker/start?target=...&returnTo=...
  DigiSvc->>DigiLocker: OAuth authorize (PKCE)
  DigiLocker-->>Frontend: User consent and redirect
  DigiLocker->>DigiSvc: GET /digilocker/callback?code&state
  DigiSvc->>DigiLocker: Exchange code, fetch docs
  DigiSvc->>DigiSvc: Store KYC in Mongo and filesystem
  Backend->>DigiSvc: GET /digilocker/kyc/:id
  DigiSvc-->>Backend: KYC payload
```

## Parent Onboard MFE token handshake
```mermaid
sequenceDiagram
  participant ParentApp
  participant MFE
  participant Backend

  ParentApp->>MFE: Load iframe /onboard
  MFE-->>ParentApp: postMessage MFE_READY
  ParentApp-->>MFE: postMessage AUTH_TOKEN
  MFE->>Backend: API calls with Bearer token
  Backend-->>MFE: 401 when token expires
  MFE-->>ParentApp: postMessage REQUEST_NEW_TOKEN
  ParentApp-->>MFE: postMessage REFRESH_TOKEN
  MFE->>Backend: Retry request
```

## Environment URLs (reference)
| Service | Prod | Dev | Notes |
| --- | --- | --- | --- |
| Backend API | `https://backend.petyosa.com` | `https://devbackend.petyosa.com` | REST under `/api/v1` |
| Auth service | `https://auth.petyosa.com` | `https://devauth.petyosa.com` | OTP gateway |
| DigiLocker backend | `https://devdigibackend.petyosa.com` | `https://devdigibackend.petyosa.com` | Same for prod and dev |
| Version Manager | `https://versions.petyosa.com` | `https://versions.petyosa.com` | Same for prod and dev |
| Parent app origin | `https://app.petyosa.com` | `https://devapp.petyosa.com` | Web app |
| Partner app origin | `https://partnerapp.petyosa.com` | `https://devpartnerapp.petyosa.com` | Web app |
| Admin app origin | `https://admin.petyosa.com` | `https://devadmin.petyosa.com` | Web app |
| Parent-onboard MFE | `https://app.petyosa.com/onboard` | `https://devapp.petyosa.com/onboard` | Embedded MFE |
