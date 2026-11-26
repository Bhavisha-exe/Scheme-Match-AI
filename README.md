
# SchemeMatch – AI-Based Government Scheme Eligibility & Recommendation Engine

## About the Project
SchemeMatch helps citizens discover government schemes that may match their personal and financial profiles.

The system uses profile-based eligibility matching, database retrieval and AI-generated explanations to simplify scheme discovery.

## Project Objectives
- Discover relevant government schemes.
- Match schemes against user profile information.
- Display matched and unmet conditions.
- Retrieve relevant scheme information from PostgreSQL.
- Generate simple AI-based explanations.
- Encourage verification through official government sources.

## How It Works
1. User enters personal profile details.
2. The backend retrieves scheme records from PostgreSQL.
3. A rule-based engine checks occupation and income conditions.
4. The retrieval component ranks relevant schemes.
5. Gemini generates explanations using retrieved scheme information.
6. Results are displayed through the frontend.

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, FastAPI
- AI Model: Google Gemini API
- Retrieval: Database-backed Retrieval-Augmented Generation (RAG)
- Database: PostgreSQL
- Deployment: GitHub Pages and Render
- Version Control: Git and GitHub

## Backend Features

- FastAPI REST API.
- PostgreSQL database integration.
- Scheme retrieval endpoint: `/schemes`
- Eligibility recommendation endpoint: `/recommend`
- AI explanation endpoint: `/explain`
- Occupation-based and income-based rule matching.
- Database-backed scheme ranking and retrieval.
- Gemini-powered explanations using retrieved scheme context.
- CORS configuration for frontend integration.

## Current Database

The prototype currently contains three illustrative scheme records:

- PM-KISAN Samman Nidhi
- National Scholarship Portal
- Ayushman Bharat PM-JAY

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend health check |
| GET | `/schemes` | Retrieve all schemes |
| POST | `/recommend` | Generate scheme recommendations |
| POST | `/explain` | Generate AI explanations using retrieved data |

## Deployment

- Frontend: https://bhavisha-exe.github.io/Scheme-Match-AI/
- Backend: https://schemematch-backend.onrender.com
- API Documentation: https://schemematch-backend.onrender.com/docs

## Team Contributions

- Bhavisha: Scheme data and knowledge base.
- Khushi: Backend development, FastAPI APIs, PostgreSQL integration, database retrieval, RAG implementation and Gemini integration.
- Shanvi: Frontend development and backend integration.

## Limitations

- Current scheme records and eligibility rules are illustrative.
- Retrieval uses PostgreSQL records and relevance scoring, not vector embeddings or FAISS/ChromaDB.
- Gemini explanations depend on API availability and quota limits.
- The current prototype checks only occupation and income conditions.
- Official eligibility, benefits and documents require independent verification.

## Disclaimer

SchemeMatch is an academic project prototype and is not an official government eligibility checker. Its recommendations do not guarantee eligibility or approval. Always verify scheme information through official government portals.

## Project Status

Working prototype with deployed frontend, FastAPI backend, PostgreSQL integration, rule-based eligibility matching and database-backed RAG retrieval.
