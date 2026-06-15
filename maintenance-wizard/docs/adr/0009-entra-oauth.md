# ADR 0009: Microsoft Entra ID OAuth

- **Status:** Accepted
- **Date:** 2026-06-07
- **Phase:** 7 (Enterprise Frontend) -- sign-in

## Context

The portal's sign-in was an Entra-styled stub (ADR 0008). The plant runs Microsoft 365,
so Microsoft Entra ID is the production identity provider. This wires a **real** Entra
authorization-code flow on the FastAPI backend while keeping the existing client-side
auth model and the persona quick-select, and while keeping the offline test suite green
without any Microsoft credentials.

## Decisions

1. **Authlib for the auth-code flow.** `backend/app/api/routers/auth.py` uses Authlib's
   Starlette `OAuth` client with OIDC discovery
   (`https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0/.well-known/openid-configuration`),
   scopes `openid profile email User.Read`. Chosen over raw MSAL for its ergonomic
   Starlette integration (redirect + token exchange + id-token parsing, with state/nonce
   handled via the session). The OAuth client is registered lazily on first use, so import
   and app creation never touch the network.

2. **Two routes.** `GET /api/auth/login` redirects the browser to Microsoft;
   `GET /api/auth/callback` (the registered `ENTRA_REDIRECT_URI`,
   `http://localhost:8000/api/auth/callback`) exchanges the code, reads the profile from
   the id-token (`name`, `preferred_username`/`email`), provisions or looks up a
   `role=engineer` / area `Finishing` user via `UserRepo.upsert`, and resolves a `user_id`.

3. **Converge on the existing client auth -- no parallel session.** The callback ends by
   redirecting the browser to `/login?uid=<user_id>`. The SPA's `LoginPage` resolves that
   id (`GET /api/me` with an `X-User-Id` override) and calls `AuthContext.login(user)` --
   the **same** path as picking a persona card. There is no server-side app session; the
   only server session is the short-lived signed cookie (`SessionMiddleware`) that Authlib
   uses to carry the OAuth state/nonce between `/login` and `/callback`.

4. **Config-driven, with graceful degradation.** All values come from settings/`.env`
   (`ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID` = `common`,
   `ENTRA_REDIRECT_URI`, plus `SESSION_SECRET`). If the client id/secret are absent, both
   routes redirect to the default engineer (`U-ENG-01`) so the portal still runs without
   OAuth configured. Every Microsoft/network call is wrapped in `try/except`; on any error
   the routes redirect to `/login?autherror=1`, which shows a clean message while the
   persona cards keep working.

5. **Tests never call Microsoft.** `conftest` forces `ENTRA_CLIENT_ID`/`SECRET` empty
   (env overrides `.env`), so the offline auth test exercises the unconfigured-fallback
   path (login/callback redirect to the default engineer) with no network. The configured
   path is verified manually against the running server (a `302` to
   `login.microsoftonline.com/.../authorize`); the live round-trip is browser-tested.

## Consequences

- Real SSO is available on `make demo` (single origin `:8000`), and the persona
  quick-select remains for fast role switching; both end in the same `AuthContext` state,
  so the rest of the app is unchanged.
- New dependencies: `authlib` and `itsdangerous` (Starlette session). `SessionMiddleware`
  is added in `create_app` with a configurable secret.
- The persona path is still credential-less by design (a demo affordance); only the
  Microsoft path authenticates. This is stated in the UI footer ("Real Microsoft Entra ID
  single sign-on") and the docs, and role gating remains UI-level, not a security boundary.
- `ENTRA_TENANT_ID=common` (multi-tenant authority, copied from the source app); pinning a
  single tenant is a one-value change if required.
