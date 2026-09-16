---
name: frontend
description: Work on the React/Vite frontend of Sistema Escuela de Futbol — starting the dev server, adding a new page/route following the flat pages+api convention, and running lint/typecheck/build. Use whenever the task touches frontend/src/.
---

# Frontend (React 19 + Vite + TypeScript + Tailwind v4)

Read `CLAUDE.md` at the repo root first for the overall architecture and the Docker-networking gotcha (Vite's dev proxy must target `localhost:8000`, not `127.0.0.1:8000`, or requests to the dockerized backend fail on this machine).

## Start it

```bash
cd frontend && npm run dev
```
Opens on `http://localhost:5173` and proxies `/api` + `/uploads` to the backend on `:8000` (see `vite.config.ts`) — the backend must already be running (`docker compose up -d postgres-db backend`). For a production-style check instead, rebuild the nginx-served container: `docker compose up -d --build frontend` (serves on `:80`).

## Add a new page

Follow the flat convention — there are no feature folders. Use an existing page as the template (`AlumnosListPage.tsx` for a list+filters+table page, `AlumnoFormPage.tsx` for a create/edit form, `MensualidadesPage.tsx` for a page with row-level actions and modals).

1. **API module** (`src/api/<resource>.ts`) — thin wrapper functions around the shared `api` axios instance (`src/api/client.ts`, which already attaches the JWT and handles 401 redirects — never construct a second axios instance).
2. **Types** — add the response shape to `src/types/index.ts` (shared) or colocate in the api module if it's only consumed by one page.
3. **Page** (`src/pages/<Name>Page.tsx`) — data fetching via `@tanstack/react-query` (`useQuery`/`useMutation`), forms via local `useState` (no form library is used in this codebase — don't introduce one), toasts via `react-hot-toast`, errors surfaced with `getErrorMessage(err, fallback)` from `src/lib/errors.ts`.
4. **Route** — lazy-import and register in `App.tsx`. Static-segment routes must come before dynamic siblings (e.g. `/alumnos/nuevo` before `/alumnos/:id`). Wrap admin-only pages in a second `<ProtectedRoute requireAdmin>` even though they're already inside the outer authenticated `<Layout>` wrapper — see `/mensualidades`, `/config`, `/usuarios` for the pattern. A page that should render outside the sidebar/nav chrome (print-friendly or public) goes as a top-level `<Route>` outside the `<Layout>`-wrapped group — see `/recibos/:pagoId` and the unauthenticated `/r/:token`.
5. **Nav link** — add to `src/components/Layout.tsx`'s `navItems` if it should appear in the sidebar (set `adminOnly: true` if relevant).

## Checks (no test runner exists — this is the full verification loop)

```bash
cd frontend
npx tsc -b --noEmit
npx eslint src
npm run build
```
Run all three before considering frontend work done. After confirming they pass, rebuild the container if the change needs to be visible outside the dev server: `docker compose up -d --build frontend`.

## Known false-positive lint rule

`react-hooks/set-state-in-effect` fires on the standard "populate controlled form state once an async query resolves" pattern (edit-mode forms loading existing data, converting a fetched blob to an object URL for an image). This codebase treats that specific pattern as a false positive — silence it with `// eslint-disable-next-line react-hooks/set-state-in-effect` and a short comment explaining why an effect is unavoidable there, rather than restructuring the component around it.

## Downloading/viewing backend-protected files

A plain `<a href>`/`<img src>` pointing at an authenticated API route (anything under `/api/...` that requires a JWT) will fail with "Not authenticated" — the browser doesn't attach the bearer token for normal navigation or image loads. Two supported patterns in this codebase:
- If the resource is already a static file served under `/uploads/...` (no auth on that mount), link to it directly.
- If it's dynamically generated (e.g. the carnet image/PDF), fetch it via the authenticated `api` client with `responseType: 'blob'`, then `URL.createObjectURL(blob)` for display/download — see `api/alumnos.ts`'s `getCarnetBlob` + `pages/CarnetPage.tsx`.
