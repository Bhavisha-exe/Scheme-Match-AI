import os
import json
import re
from pathlib import Path
from typing import Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ---------- Configuration ----------
BASE_DIR = Path(__file__).resolve().parent
SCHEMES_FILE = BASE_DIR / "schemes.json"
RULES_FILE = BASE_DIR / "eligibility_rules.json"
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    gemini_client = None

app = FastAPI(
    title="SchemeMatch API",
    description="Government scheme discovery, eligibility matching and AI explanations"
)
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

# New catalog tables avoid destructive changes to the old three-column demo table.
class Scheme(Base):
    __tablename__ = "scheme_catalog"
    id = Column(Integer, primary_key=True)
    scheme_id = Column(String(40), unique=True, index=True, nullable=False)
    name = Column(String(500), nullable=False)
    category = Column(String(300), default="")
    description = Column(Text, default="")
    benefits = Column(Text, default="")
    eligibility = Column(Text, default="")
    application_process = Column(Text, default="")
    documents_required = Column(Text, default="")
    faqs = Column(Text, default="")
    official_source_url = Column(Text, default="")

class EligibilityRule(Base):
    __tablename__ = "scheme_eligibility_rules"
    id = Column(Integer, primary_key=True)
    scheme_id = Column(String(40), unique=True, index=True, nullable=False)
    minimum_age = Column(String(200), default="")
    maximum_age = Column(String(200), default="")
    maximum_annual_income = Column(String(300), default="")
    eligible_occupation = Column(Text, default="")
    eligible_location = Column(Text, default="")
    other_conditions = Column(Text, default="")

class UserProfile(BaseModel):
    age: int
    income: float
    occupation: str
    state: str
    category: str
    gender: str


def load_json(path: Path):
    if not path.exists():
        raise RuntimeError(f"Required data file is missing: {path.name}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def import_dataset():
    schemes_data = load_json(SCHEMES_FILE)
    rules_data = load_json(RULES_FILE)
    rules_by_id = {str(r.get("Scheme ID", "")).strip(): r for r in rules_data}
    db = SessionLocal()
    try:
        for item in schemes_data:
            sid = str(item.get("Scheme ID", "")).strip()
            if not sid:
                continue
            row = db.query(Scheme).filter_by(scheme_id=sid).first()
            if row is None:
                row = Scheme(scheme_id=sid)
                db.add(row)
            row.name = item.get("Scheme Name", "")
            row.category = item.get("Category", "")
            row.description = item.get("Description", "")
            row.benefits = item.get("Benefits", "")
            row.eligibility = item.get("Eligibility", "")
            row.application_process = item.get("Application Process", "")
            row.documents_required = item.get("Documents Required", "")
            row.faqs = item.get("FAQs", "")
            row.official_source_url = item.get("Official Source URL", "")
            rule = rules_by_id.get(sid)
            if rule:
                rr = db.query(EligibilityRule).filter_by(scheme_id=sid).first()
                if rr is None:
                    rr = EligibilityRule(scheme_id=sid)
                    db.add(rr)
                rr.minimum_age = str(rule.get("Minimum Age", ""))
                rr.maximum_age = str(rule.get("Maximum Age", ""))
                rr.maximum_annual_income = str(rule.get("Maximum Annual Income", ""))
                rr.eligible_occupation = str(rule.get("Eligible Occupation", ""))
                rr.eligible_location = str(rule.get("Eligible Location", ""))
                rr.other_conditions = str(rule.get("Other Conditions", ""))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    import_dataset()

@app.get("/")
def home():
    return {"message": "SchemeMatch Backend is running!", "database": "PostgreSQL connected"}

@app.get("/schemes")
def get_schemes():
    db = SessionLocal()
    try:
        rows = db.query(Scheme).order_by(Scheme.scheme_id).all()
        return [{
            "scheme_id": s.scheme_id, "name": s.name, "category": s.category,
            "description": s.description, "benefits": s.benefits,
            "eligibility": s.eligibility, "documents_required": s.documents_required,
            "application_process": s.application_process, "faqs": s.faqs,
            "official_source_url": s.official_source_url
        } for s in rows]
    finally:
        db.close()


def occupation_relevant(profile_occupation: str, eligible_occupation: str) -> bool:
    text = (eligible_occupation or "").lower()
    occ = (profile_occupation or "").lower().strip()
    if not text or "all occupations" in text or "any occupation" in text or text.strip() == "any":
        return True
    aliases = {
        "farmer": ["farmer", "agricultur", "cultivator", "grower", "landholding"],
        "student": ["student", "school", "college", "education", "scholarship"],
        "self-employed": ["self-employed", "entrepreneur", "business", "vendor", "artisan"],
        "woman": ["woman", "women", "female"],
    }
    terms = aliases.get(occ, [occ])
    return any(term in text for term in terms)


def income_limit(value: str) -> Optional[float]:
    text = (value or "").lower()
    if not text or "no fixed" in text or "no income" in text or "no limit" in text:
        return None
    nums = re.findall(r"\d[\d,]*(?:\.\d+)?", text.replace(",", ""))
    if not nums:
        return None
    try:
        return float(nums[0])
    except ValueError:
        return None

@app.post("/recommend")
def recommend(profile: UserProfile):
    db = SessionLocal()
    try:
        rows = db.query(Scheme).all()
        rule_rows = {r.scheme_id: r for r in db.query(EligibilityRule).all()}
        results = []
        for s in rows:
            r = rule_rows.get(s.scheme_id)
            occupation = r.eligible_occupation if r else ""
            if not occupation_relevant(profile.occupation, occupation):
                continue
            matched, unmet = [], []
            if occupation:
                matched.append("Occupation is consistent with the scheme rule; verify detailed conditions")
            else:
                matched.append("Occupation condition needs official verification")
            max_income = income_limit(r.maximum_annual_income if r else "")
            if max_income is not None:
                if profile.income <= max_income:
                    matched.append("Income is within the stated limit")
                else:
                    unmet.append("Income exceeds the stated limit")
            else:
                matched.append("No fixed income ceiling identified in the supplied rule")
            # Age, location, category and other criteria are shown for human/official verification;
            # free-text source rules are not treated as conclusively satisfied by this prototype.
            results.append({
                "scheme_id": s.scheme_id, "scheme": s.name, "category": s.category,
                "eligible": False,
                "status": "Potential match - further eligibility verification required",
                "matched_conditions": matched, "unmet_conditions": unmet,
                "age_rule": r.minimum_age if r else "",
                "maximum_age_rule": r.maximum_age if r else "",
                "income_rule": r.maximum_annual_income if r else "",
                "occupation_rule": occupation,
                "location_rule": r.eligible_location if r else "",
                "other_conditions": r.other_conditions if r else s.eligibility,
                "benefit": s.benefits, "documents_required": s.documents_required,
                "application_process": s.application_process,
                "official_source_url": s.official_source_url
            })
        return {"status": "success", "total_schemes": len(results), "recommendations": results}
    finally:
        db.close()

@app.post("/explain")
def explain(profile: UserProfile):
    db = SessionLocal()
    try:
        all_schemes = db.query(Scheme).all()
        rules = {r.scheme_id: r for r in db.query(EligibilityRule).all()}
        relevant = []
        for s in all_schemes:
            r = rules.get(s.scheme_id)
            if occupation_relevant(profile.occupation, r.eligible_occupation if r else ""):
                relevant.append({"scheme_id": s.scheme_id, "name": s.name, "category": s.category,
                                 "benefits": s.benefits, "eligibility": s.eligibility,
                                 "occupation_rule": r.eligible_occupation if r else "",
                                 "income_rule": r.maximum_annual_income if r else "",
                                 "location_rule": r.eligible_location if r else "",
                                 "other_conditions": r.other_conditions if r else ""})
        if not gemini_client:
            return {"explanation": "AI explanation is unavailable because GEMINI_API_KEY is not configured.", "retrieved_schemes": relevant}
        prompt = f"""You are SchemeMatch, an Indian government scheme information assistant.
User profile: age={profile.age}, income=₹{profile.income}, occupation={profile.occupation}, state={profile.state}, category={profile.category}, gender={profile.gender}.
Use ONLY the retrieved records below. Explain possible matches simply. Do not claim confirmed eligibility. Clearly say that age, location, category and other conditions must be checked against official sources. Do not invent facts.
Retrieved records: {json.dumps(relevant, ensure_ascii=False)}"""
        try:
            response = gemini_client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
            explanation = response.text or "AI explanation is temporarily unavailable."
        except Exception as e:
            msg = str(e)
            explanation = ("Gemini API request quota has been reached. Please try again after the quota resets."
                           if "429" in msg or "RESOURCE_EXHAUSTED" in msg else
                           "AI explanation is temporarily unavailable. Please try again later.")
        return {"explanation": explanation, "retrieved_schemes": relevant}
    finally:
        db.close()
