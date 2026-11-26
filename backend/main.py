import os
from fastapi import FastAPI
from google import genai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="SchemeMatch API",
    description="Government Scheme Eligibility and Recommendation Engine"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://bhavisha-exe.github.io",
    "https://schemematch-backend.onrender.com"
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


# Database table
class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    max_income = Column(Float, nullable=False)
    benefit = Column(String, nullable=False)


# Initial demo scheme records
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
        "database": "PostgreSQL connected"
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


@app.post("/recommend")
def recommend(profile: UserProfile):
    db = SessionLocal()

    try:
        schemes = db.query(Scheme).all()
        results = []

        for scheme in schemes:
            matched = []
            unmet = []

            if (
                scheme.occupation == "Any"
                or scheme.occupation.lower() == profile.occupation.lower()
            ):
                matched.append("Occupation condition matched")
            else:
                unmet.append("Occupation condition not matched")

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

@app.post("/explain")
def explain(profile: UserProfile):
    prompt = f"""
    You are SchemeMatch, a government scheme assistant.

    Explain these user details in simple language:
    Age: {profile.age}
    Income: ₹{profile.income}
    Occupation: {profile.occupation}
    State: {profile.state}
    Category: {profile.category}
    Gender: {profile.gender}

    Explain that eligibility must be verified using official government
    sources. Do not invent scheme benefits or eligibility rules.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {"explanation": response.text}

    except Exception as e:
        return {
            "error": "AI explanation unavailable",
            "details": str(e)
        }
