# PULSEIQ Aurora — React + FastAPI + Supabase

**This is the main application codebase.** The previous `kaki.html` interface is kept only under `design/` for reference; the running UI is React. UI inspiration: the approved blue/teal/purple PULSEIQ concept slides, redesigned as real components rather than static screenshots. Animated card float, halo backlight, gradient backgrounds and slow moving light-bars are implemented in CSS with reduced-motion support.

## Start here

**Production / Render:** deploy this entire `PULSE/` directory from the repository root with the included `Dockerfile` and `render.yaml`. The Docker build compiles React, installs FastAPI/scikit-learn dependencies, and serves both under one origin. `https://your-render-service.onrender.com/health` must return `status: ok`.

### Render environment (secrets live on Render only)

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Supabase PostgreSQL **Session pooler** URI copied from Supabase → Connect; include username `postgres.PROJECT_REF`, correct database password, `?sslmode=require` |
| `APP_SECRET` | Yes | At least 32 random characters; Render can generate |
| `BOOTSTRAP_COLLEGE_NAME` | For original demo bootstrap | Institution name (e.g. `Demo Engineering College`) |
| `BOOTSTRAP_COLLEGE_DOMAIN` | For original demo bootstrap | Match `pi3_colleges.domain` (for example `democollege.edu.in`) |
| `BOOTSTRAP_ADMIN_EMAIL` | For original demo bootstrap | Admin address from the same college domain |
| `BOOTSTRAP_ADMIN_PASSWORD` | For original demo bootstrap | 12+ random characters |
| `REGISTRATION_INVITE_CODE` | To allow additional colleges | Strong random platform invite secret supplied to authorized college registrants |
| `COOKIE_SECURE` | In production | `true` |
| `SEED_DEMO` | Optional | Recommended `false` |
| `IMPORT_LEGACY_V2` | Optional | Recommended `false` |

You may **either** configure bootstrap admin variables to create the initial college **or**, for a completely new PostgreSQL instance, configure a registration invite code and leave all bootstrap variables unset. Do not disable `COOKIE_SECURE` on HTTPS Render deployments. Never put a database URL, an invite code, or API secrets in `frontend/`.

**Supabase database password format**: use the exact *Session pooler* connection string from Supabase, which commonly looks like `postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require`. URL-encode special characters in your password. Do not put just `db.PROJECT_REF.supabase.co` in `DATABASE_URL`.

### Run locally on Windows

Install Python 3.12 and Node.js 24. In PowerShell:

```powershell
# In the PULSE folder. Replace all example values privately.
$env:DATABASE_URL = 'postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=require'
$env:APP_SECRET = 'REPLACE_WITH_A_RANDOM_VALUE_LONGER_THAN_32_CHARACTERS'
$env:BOOTSTRAP_COLLEGE_NAME = 'Demo Engineering College'
$env:BOOTSTRAP_COLLEGE_DOMAIN = 'democollege.edu.in'
$env:BOOTSTRAP_ADMIN_EMAIL = 'admin@democollege.edu.in'
$env:BOOTSTRAP_ADMIN_PASSWORD = 'REPLACE_WITH_PRIVATE_LONG_RANDOM_PASSWORD'
$env:REGISTRATION_INVITE_CODE = 'REPLACE_WITH_PRIVATE_LONG_INVITE_CODE'
$env:COOKIE_SECURE = 'false'  # localhost only
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-connectors.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

In a **second** terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to FastAPI. Or run `start_windows.bat` after setting env vars in your Command Prompt.

## Access & workflows

| Portal | Live database functionality |
|---|---|
| New college | Secure invite-only self registration with own admin account; independent college domain, preferences, brand accent, academic calendar, departments, grading scheme, attendance target, request/risk toggles |
| Admin | All-college roster, add/edit students, faculty/user account creation and password resets, enable/disable accounts, faculty class assignment, attendance and marks publishing, announcements, interventions, requests, timetable, analytics, ML training, source import, audit, learning assignments/tests, resources |
| Faculty | Their own assigned classes, student roster, attendance and marks entry, assigned subject performance, student focus insights, interventions, create coursework/MCQ quizzes/resources, view submissions and manually grade written assignments |
| Student | Only their own profile and student records, approved marks and attendance, published subject tasks, take auto-graded MCQ quizzes, submit written assignments, view grading feedback, resources/links, personalized focus areas, support requests |

**Critical first-run setup for the user's existing demo**: `public.students` has 250 rows and `public.faculty` has 20, but they do NOT become login accounts automatically. The existing roster may already contain 250 rows in `pi3_roster`. Go to Admin → **Supabase Import** and provide faculty/student temporary passwords (12+ characters) to populate `pi3_accounts`. The import matches the **source college's** `public.colleges.email_domain` to the **application college's** `pi3_colleges.domain`; for this instance both should be `democollege.edu.in`. Student addresses at `@demo.edu.in` can remain unchanged. No existing passwords are overwritten. Admin must verify and add teaching assignments for department, semester, section and subject before faculty can see their students.

Run `database/02_check_database.sql` in Supabase SQL Editor for record counts. `database/01_application_schema.sql` is an optional manual schema script; normally FastAPI creates the missing `pi3_*` tables on startup. Do **not** disable RLS to fix import visibility; FastAPI uses a direct private PostgreSQL connection. Protect the database password and do not expose `pi3_accounts` over the Supabase public Data API.

## IMPORTANT: college isolation vs. separate database

This release is a **single hosted Supabase PostgreSQL database with per-college `college_id` isolation** across the application's 20 `pi3_*` tables. Colleges get separate institution workspaces and private data access checks. **It does not create a physical Supabase database/project for each college.** The existing External Data Sources module supports selected college-owned data connections for importing records, but application tables still live in the shared hosted database. Real database-per-tenant provisioning would require a separate database-provisioning control plane, migration orchestration, per-tenant connection lifecycle, backups, and security review before it can be advertised. For the hackathon/demo, the secure shared tenant pattern is the supported architecture.

**Self-registration is invite-only, not domain-verified:** a platform administrator controls who receives `REGISTRATION_INVITE_CODE`. Before public production registration, add email/domain ownership verification, invite expiry/rotation, moderation, rate limiting, tenant quotas, legal consent and operational monitoring. The code enforces role permissions, college ID scoping, HttpOnly session cookies, same-site CSRF, Argon2 password hashing, restricted CORS and audit logs, but those protections do not replace a security review.

## 7 data categories and success score

`backend/scoring.py` calculates a transparent rule-based score from **fresh observations** in these seven categories:

- Academic: marks, backlog count (backlogs drive risk rules)
- Attendance: attended / held class records
- LMS: completed / assigned activities
- Engagement: campus activities completed
- Placement: aptitude, coding and interviews
- Skills: technical and communication assessments
- Feedback: help requested and contextual sentiment/support information, shown alongside scoring **but not currently included in weighted numerical score**

**Weighted Student Success Score (6 numerical components)** from `backend/config.json`: Academic 30%, Attendance 20%, LMS 15%, Placement 25%, Skills 5%, Engagement 5%. Coverage must be at least 80% for a provisional score; absent data stays unscored. The feedback category is available as an observation and can influence contextual recommendations but is **not** part of the current score formula. The academic/placement support flags are explainable rules, not ML predictions.

**Traditional ML** (`backend/traditional_ml.py`) uses scikit-learn RandomForest with 7 features: marks %, attendance %, LMS %, placement %, skills %, engagement %, and backlogs. The model needs at least 40 labeled historical observations, including both outcome classes; labels must be from an actual **later** outcome to prevent leakage. An explicit synthetic demo training option is available and is never claimed as real validation. Holdout ROC-AUC, accuracy, precision, recall and feature importances are displayed. The model artifact lives in `pi3_ml_models` by college. `GET /api/insights/focus` supplies immediate evidence-based guidance using observed gaps and institution attendance preferences; it is not causal future-boost prediction.

## Testing and limitations

The backend automated integration smoke flow exercised **college registration, invalid invite refusal, login, preferences, add student, add faculty/student accounts, class assignment, create quiz, student quiz completion/autograde, duplicate submission blocking, resources, explainable focus API, roles, and cross-college isolation**. Tests passed with an SQLite test engine and a local *test-only* Argon2-compatible stand-in for `pwdlib` (which was missing from the execution environment). `python -m compileall -q backend` passed and TypeScript/JSX syntax parsing passed. Synthetic RandomForest training and predictions also ran successfully.

**Not verified**: a complete npm production build in this offline environment, actual Render deployment, connectivity using your private Supabase credentials, browser-click end-to-end tests, simultaneous many-college load, mobile layouts on physical devices, production domain verification and per-tenant physical database provisioning. These require a deployment environment and credentials. The Dockerfile is set up to execute `npm ci && npm run build` during Render build; failures should be addressed from actual Render build logs.

Current scope excludes file upload storage for student assignments (written response and link sharing are implemented), AI-created free-form question banks, LLM content generation, automatic external data connectors for every campus vendor, accreditation exports, PDF slides, automatic scheduled ML retraining, and separate database per college. Those are extension points, not working features in this ZIP.

See `docs/API.md` for the original endpoints and `backend/learning.py` and `backend/college_setup.py` for the newly added endpoints. Do not use fake numeric KPIs in demonstrations; if Supabase contains no observation data, the analytics correctly show missing/insufficient evidence.
