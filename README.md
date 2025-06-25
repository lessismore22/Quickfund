# QuickCash - Micro-Lending Platform

## System Overview

QuickCash is a modern micro-lending platform designed for the Nigerian market, providing instant loan approvals and seamless repayment experiences.

### Tech Stack

* **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS
* **Backend**: Django 4.2, Django REST Framework
* **Database**: PostgreSQL with Redis for caching
* **Authentication**: JWT with refresh tokens
* **Payment**: Paystack integration for Nigerian market
* **Infrastructure**: Docker, AWS/GCP, Nginx
* **Monitoring**: Prometheus, Grafana, Sentry

## Architecture Diagram

```
┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
│   Frontend      │    │   API Gateway   │    │   Backend       │
│   (Next.js)     │◄─▶│   (Nginx)       │◄─▶│   (Django)      │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────────┐
         │                       │              │   Database      │
         │                       │              │   (PostgreSQL)  │
         │                       │              └─────────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────────┐
         │                       │              │   Cache/Queue   │
         │                       │              │   (Redis)       │
         │                       │              └─────────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────┐    ┌─────────────────────┐
│   CDN           │    │   Load Balancer │
│   (CloudFront)  │    │   (ALB)         │
└─────────────────────┘    └─────────────────────┘
```

## Database Schema

*See full schema definitions in [`schema.sql`](./docs/schema.sql)*

## API Endpoints

*See all API routes and usage examples in [`API_DOCS.md`](./docs/API_DOCS.md)*

## Security Implementation

* JWT-based auth with refresh token rotation
* Role-based permissions
* Input validation with DRF serializers
* Rate limiting with `UserRateThrottle` & `AnonRateThrottle`

## Frontend Highlights

* React + TypeScript-based form validation
* TailwindCSS for responsive UI
* Loan dashboard for user-specific applications

## Credit Scoring

Dynamic scoring between 300–850 based on:

* Income
* Debt-to-income ratio
* Employment stability
* Loan history
* External signals

## Deployment & DevOps

* **Dockerized** services for backend, frontend, Redis, PostgreSQL
* **GitHub Actions** for CI/CD pipelines
* Deployed via **ECS/EKS** (or GCP equivalent)

## Monitoring

* Prometheus & Grafana for metrics and alerts
* Sentry for error tracking and performance

## Nigerian Market Specifics

* Paystack integration for NGN payments
* BVN verification via CBN-compliant vendors
* Termii/SMSLive247 for SMS alerts
* Compliant with **NDPR**, **KYC/AML**, and **CBN** regulations

## Performance Optimization

* DB indexing (email, phone, status, etc.)
* Redis caching for sessions and query results
* API response caching
* Frontend: lazy loading, code splitting, and service workers

## Security Checklist

* [x] Secure password hashing
* [x] CSRF/XSS/SQLi prevention
* [x] HTTPS & HSTS
* [x] PII encryption
* [x] Audit logging

## Compliance

* NDPR (Nigeria)
* PCI DSS (Payment)
* ISO 27001
* GDPR (Data handling)

## License

[MIT](./LICENSE)

---

**QuickCash** is built for financial inclusion, aiming to simplify access to credit in emerging markets.
