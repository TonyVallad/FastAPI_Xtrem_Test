# 🚀 Project Roadmap – SAS IA FastAPI Xtrem (API Version PRO)

---

## 🔧 Phase 0 – Environment Setup & Structuring (Days 1–2)

**Objectives:**
- Form teams and define roles (Scrum Master & Product Owner)
- Setup dev environment and repositories

**Tasks:**
1. Team formation, SM & PO designation  
2. Create virtualenv and initialize:
   - `requirements.txt`
   - `.env` (sensitive vars)
   - `README.md`  
3. GitHub repo setup with versioning (`v0`)
4. Basic FastAPI “Hello World” route

**Deliverables:**
- Team structure defined
- Project repo initialized and pushed (`v0`)
- Working FastAPI app accessible via `/docs`

---

## 🧱 Phase 1 – Modular Architecture (Day 3)

**Objectives:**
- Establish modular codebase

**Tasks:**
1. Create directory structure:
   - `main.py`
   - `users/routes.py`
   - `db/routes.py`  
2. Ensure clean imports and functionality

**Deliverables:**
- Modularized, organized FastAPI project
- GitHub commit `v0.0.1`

---

## 🗄️ Phase 2 – Database & Models (Days 4–5)

**Objectives:**
- Design and integrate a relational database schema

**Tasks:**
1. Design MCD → MLD → MPD
2. Create:
   - SQLAlchemy models
   - Pydantic schemas  
3. Setup DB lifecycle hooks via `add_event_handler`
4. Log events with Loguru

**Deliverables:**
- Working DB connection (SQLite)
- Schemas and models implemented
- Initial CRUD routes: login/logout

---

## 🎨 Phase 3 – Frontend (Streamlit) & API Split (Days 6–7)

**Objectives:**
- Integrate a user-friendly interface

**Tasks:**
1. Create `api/` and `frontend/` folders
2. Build `frontend/pages/0_login.py` with:
   - Signup/login forms
   - Field validation (email, password)
3. API side:
   - Hash password storage
   - Signup/login/logout routes

**Deliverables:**
- Streamlit login page functional
- Users can register and login through frontend/backend
- API and frontend fully separated

---

## 🧪 Phase 4 – Testing and First Release (Days 8–9)

**Objectives:**
- Add testing coverage, release `v0.1`

**Tasks:**
1. Setup `pytest`
2. Write tests for:
   - DB connection
   - User registration/login/delete
3. Encrypt sensitive user data
4. Prepare docs and screenshots

**Deliverables:**
- Functional tests run via `pytest`
- Sensitive data encrypted
- GitHub Release `v0.1`

---

## 🧍 Phase 5 – User Profile & Admin (Day 10)

**Objectives:**
- Add user enrichment and admin tools

**Tasks:**
1. Add fields to user model:
   - Pseudo, bio, role, etc.
2. Add:
   - Modify profile
   - Delete account
   - Admin view of users (via `/admin` page in Streamlit)

**Deliverables:**
- Full user profile management
- Admin dashboard working

---

## 🔐 Phase 6 – Authentication (Days 11–13)

**Objectives:**
- Secure API using OAuth2 & JWT

**Tasks:**
1. Refactor project for security integration
2. Implement:
   - `OAuth2PasswordBearer`
   - JWT token generation
   - Role-based access (basic at this stage)
3. Add `security.py`, Docker support
4. GitHub Release `v0.2`

**Deliverables:**
- JWT-based login with token returns
- Secure routes
- Dockerfile and docker-compose.yaml
- Pushed release `v0.2`

---

## 🛂 Phase 7 – Scopes & Permissions (Day 14)

**Objectives:**
- Introduce granular access control

**Tasks:**
1. Define scopes (e.g. `user:read`, `admin:write`)
2. Update route protection logic
3. Validate role-based restrictions

**Deliverables:**
- Scopes implemented and enforced
- Tests for restricted routes

---

## 🔁 Phase 8 – Secure Token Rotation (Day 15)

**Objectives:**
- Add refresh token rotation

**Tasks:**
1. Model for storing refresh tokens
2. Auto-rotate tokens on access renewal
3. Invalidate old tokens

**Deliverables:**
- Refresh token system working
- Secure rotation verified with tests

---

## 📊 Phase 9 – Logging & Monitoring (Days 16–17)

**Objectives:**
- Add observability & audit logs

**Tasks:**
1. Use Loguru to:
   - Log logins, logouts, failed attempts
   - Timestamped, clean logs
2. Setup Docker Compose stack with:
   - Prometheus
   - Grafana
3. Expose `/health` route
4. (Bonus) Configure Grafana alerts

**Deliverables:**
- Logging visible and persistent
- Monitoring dashboard accessible
- Health route available

---

## 🚢 Phase 10 – Finalization & Production (Day 18)

**Objectives:**
- Polish and ship the project

**Tasks:**
1. Final cleanup & code quality review
2. Complete and polish README:
   - Installation
   - Dev & prod instructions
   - API usage guide
3. Tag final release `v0.2`
4. Prepare pitch/demo if needed

**Deliverables:**
- Fully working and secure FastAPI/Streamlit app
- Production-ready documentation
- Final GitHub push and tag

---

## ⏱️ Summary Timeline (Estimated Duration: ~3 weeks)

| Phase                          | Estimated Duration |
|-------------------------------|--------------------|
| Setup & Structuring           | 2 days             |
| Modular Architecture          | 1 day              |
| Database + Models             | 2 days             |
| API + Frontend Integration    | 2 days             |
| Testing + Release v0.1        | 2 days             |
| User Profiles + Admin View    | 1 day              |
| Authentication + Release v0.2| 3 days             |
| Scopes & Permissions          | 1 day              |
| Token Rotation                | 1 day              |
| Logs & Monitoring             | 2 days             |
| Finalization & Deployment     | 1 day              |

---

## 📌 Tips for Project Success

- Hold daily stand-ups with SM to track progress
- Use Trello or Jira to organize sprint tasks
- Make small, regular commits
- Always document new features and changes in `README.md`
- Use GitHub Issues to track bugs and improvements