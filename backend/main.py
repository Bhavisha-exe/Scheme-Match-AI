
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY else None
)

app = FastAPI(
    title="SchemeMatch API",
    description="AI-Based Government Scheme Eligibility and Recommendation Engine"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bhavisha-exe.github.io",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Database model
class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    max_income = Column(Float, nullable=False)
    benefit = Column(String, nullable=False)


# Initial demo records
initial_schemes = [
    {
        "name": "PM-KISAN Samman Nidhi",
        "occupation": "Farmer",
        "max_income": 999999999,
        "benefit": "Financial support of ₹6,000 per year"
    },
    {
        "name": "National Scholarship Portal",
        "occupation": "Student",
        "max_income": 800000,
        "benefit": "Scholarship assistance"
    },
    {
        "name": "Ayushman Bharat PM-JAY",
        "occupation": "Any",
        "max_income": 999999999,
        "benefit": "Eligible families can receive health coverage"
    }
]


@app.on_event("startup")
def setup_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_names = {
            name for (name,) in db.query(Scheme.name).all()
        }

        for item in initial_schemes:
            if item["name"] not in existing_names:
                db.add(Scheme(**item))

        db.commit()
    finally:
        db.close()


# User profile
class UserProfile(BaseModel):
    age: int
    income: float
    occupation: str
    state: str
    category: str
    gender: str


@app.get("/")
def home():
    return {
        "message": "SchemeMatch Backend is running!",
        "database": "PostgreSQL connected",
        "retrieval": "Database-backed RAG enabled"
    }


@app.get("/schemes")
def get_schemes():
    db = SessionLocal()
    try:
        records = db.query(Scheme).all()

        return [
            {
                "name": s.name,
                "occupation": s.occupation,
                "benefit": s.benefit
            }
            for s in records
        ]
    finally:
        db.close()


# Database retrieval for RAG
def retrieve_relevant_schemes(profile: UserProfile):
    db = SessionLocal()

    try:
        schemes = db.query(Scheme).all()
        ranked_schemes = []

        for scheme in schemes:
            score = 0

            # Occupation relevance
            if scheme.occupation.lower() == profile.occupation.lower():
                score += 3
            elif scheme.occupation.lower() == "any":
                score += 1

            # Income relevance
            if profile.income <= scheme.max_income:
                score += 2

            # Scheme name and benefit keyword relevance
            profile_words = set(
                profile.occupation.lower().split()
            )

            scheme_text = (
                scheme.name + " " + scheme.benefit
            ).lower()

            for word in profile_words:
                if len(word) > 2 and word in scheme_text:
                    score += 1

            ranked_schemes.append({
                "name": scheme.name,
                "occupation": scheme.occupation,
                "maximum_income": scheme.max_income,
                "benefit": scheme.benefit,
                "relevance_score": score
            })

        ranked_schemes.sort(
            key=lambda item: item["relevance_score"],
            reverse=True
        )

        return ranked_schemes[:5]

    finally:
        db.close()


# Eligibility recommendation endpoint

@app.post("/recommend")
def recommend(profile: UserProfile):
    db = SessionLocal()

    try:
        schemes = db.query(Scheme).all()
        results = []

        for scheme in schemes:

            # Filter by occupation
            occupation_match = (
                scheme.occupation.lower() == "any"
                or scheme.occupation.lower() == profile.occupation.lower()
            )

            if not occupation_match:
                continue

            matched = []
            unmet = []

            matched.append("Occupation condition matched")

            # Check income
            if profile.income <= scheme.max_income:
                matched.append("Income condition matched")
            else:
                unmet.append("Income condition not matched")

            eligible = len(unmet) == 0

            results.append({
                "scheme": scheme.name,
                "eligible": eligible,
                "status": (
                    "Eligible" if eligible
                    else "Needs further checking"
                ),
                "matched_conditions": matched,
                "unmet_conditions": unmet,
                "benefit": scheme.benefit
            })

        return {
            "status": "success",
            "total_schemes": len(results),
            "recommendations": results
        }

    finally:
        db.close()



# RAG-based AI explanation endpoint
@app.post("/explain")
def explain(profile: UserProfile):

    # Step 1: Retrieve relevant schemes from PostgreSQL
    retrieved_schemes = retrieve_relevant_schemes(profile)

    if not retrieved_schemes:
        return {
            "explanation": "No scheme information was found in the database.",
            "retrieved_schemes": []
        }

    if client is None:
        return {
            "explanation": "AI explanation is unavailable. Gemini API key is not configured.",
            "retrieved_schemes": retrieved_schemes
        }

    # Step 2: Prepare retrieved database context
    scheme_context = "\n".join([
        (
            f"Scheme: {scheme['name']}\n"
            f"Occupation: {scheme['occupation']}\n"
            f"Maximum income in database: ₹{scheme['maximum_income']}\n"
            f"Recorded benefit: {scheme['benefit']}\n"
            f"Retrieval relevance score: {scheme['relevance_score']}"
        )
        for scheme in retrieved_schemes
    ])

    # Step 3: Build grounded prompt
    prompt = f"""
You are SchemeMatch, an AI government scheme information assistant.

USER PROFILE:
Age: {profile.age}
Income: ₹{profile.income}
Occupation: {profile.occupation}
State: {profile.state}
Category: {profile.category}
Gender: {profile.gender}

RETRIEVED SCHEME INFORMATION FROM THE POSTGRESQL DATABASE:
{scheme_context}

TASK:
1. Explain the user's profile in simple language.
2. Explain which retrieved schemes may be relevant and why.
3. Use only the scheme information provided above.
4. Do not invent eligibility conditions, documents, deadlines,
   benefits, or government rules.
5. Clearly explain that the database contains limited demo criteria.
6. Do not guarantee eligibility or approval.
7. Tell the user to verify final eligibility using official
   government sources.

Write a short, clear explanation in simple language.
"""

    # Step 4: Generate AI explanation
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return {
            "explanation": response.text or
                "AI could not generate an explanation.",
            "retrieved_schemes": retrieved_schemes,
            "retrieval_method": "PostgreSQL database retrieval"
        }

    except Exception as e:
        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            message = (
                "Gemini API request quota has been reached. "
                "Please try again after the quota resets."
            )
        else:
            message = (
                "AI explanation is temporarily unavailable. "
                "Please try again later."
            )

        return {
            "explanation": message,
            "retrieved_schemes": retrieved_schemes,
            "error": error_message
        }
