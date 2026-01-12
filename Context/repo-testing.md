# Testing Repos and QA Assets

## Frontend/parent-testing
- Mirror of Frontend/parent with testing specific env and docs.
- Same CRA stack and build assets (Dockerfile, cloudbuild.yaml, nginx.conf).
- Used for testing features without impacting main app.

## Frontend/partner-testing
- Mirror of Frontend/partner with similar stack and config.
- Includes capacitor and capacitor-production branches locally.

## Jmeter
- JMeter plans under Jmeter/*.jmx
- Test reports under Jmeter/Test Reports/...

## Notes
These repos are useful for load testing, UI regression checks, and staging flows.
