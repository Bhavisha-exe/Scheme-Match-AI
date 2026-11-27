
import os
import json
import re
from pathlib import Path
from typing import Optional, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, JSON,
    text
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------- Configuration ----------

BASE_DIR = Path(__file__).resolve().parent
SCHEMES_FILE = BASE_DIR / "schemes.json"
RULES_FILE = BASE_DIR / "eligibility_rules.json"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

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


# ---------- Database Models ----------

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
    official_url = Column(Text, default="")


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

    eligibility_source_url = Column(Text, default="")
    verification_status = Column(String(50), default="needs_review")
    verified_eligibility_criteria = Column(JSON, default=list)


class UserProfile(BaseModel):
    age: int
    income: float
    occupation: str
    state: str
    category: str
    gender: str


# ---------- JSON Helpers ----------

def load_json(path: Path):
    if not path.exists():
        raise RuntimeError(f"Required data file is missing: {path.name}")

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def json_safe(value):
    if value is None:
        return []
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (list, dict)):
                return parsed
        except (ValueError, TypeError):
            pass
        return [value] if value.strip() else []
    return [value]


def migrate_database():
    """Add new columns safely to existing PostgreSQL tables."""

    migrations = [
        """
        ALTER TABLE scheme_catalog
        ADD COLUMN IF NOT EXISTS official_url TEXT DEFAULT ''
        """,
        """
        ALTER TABLE scheme_eligibility_rules
        ADD COLUMN IF NOT EXISTS eligibility_source_url TEXT DEFAULT ''
        """,
        """
        ALTER TABLE scheme_eligibility_rules
        ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50)
        DEFAULT 'needs_review'
        """,
        """
        ALTER TABLE scheme_eligibility_rules
        ADD COLUMN IF NOT EXISTS verified_eligibility_criteria JSON
        DEFAULT '[]'
        """
    ]

    with engine.begin() as connection:
        for migration in migrations:
            connection.execute(text(migration))


# ---------- Import 45 Schemes ----------

def import_dataset():
    schemes_data = load_json(SCHEMES_FILE)
    rules_data = load_json(RULES_FILE)

    if not isinstance(schemes_data, list) or not isinstance(rules_data, list):
        raise RuntimeError("Both JSON files must contain arrays of records.")

    rules_by_id = {
        str(r.get("Scheme ID", "")).strip(): r
        for r in rules_data
    }

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

            url = (
                item.get("official_url")
                or item.get("Official Source URL")
                or item.get("official_source_url")
                or ""
            )

            row.official_url = url
            row.official_source_url = (
                item.get("Official Source URL") or url
            )

            rule = rules_by_id.get(sid)

            if rule:
                rr = db.query(EligibilityRule).filter_by(
                    scheme_id=sid
                ).first()

                if rr is None:
                    rr = EligibilityRule(scheme_id=sid)
                    db.add(rr)

                rr.minimum_age = str(rule.get("Minimum Age", ""))
                rr.maximum_age = str(rule.get("Maximum Age", ""))
                rr.maximum_annual_income = str(
                    rule.get("Maximum Annual Income", "")
                )
                rr.eligible_occupation = str(
                    rule.get("Eligible Occupation", "")
                )
                rr.eligible_location = str(
                    rule.get("Eligible Location", "")
                )
                rr.other_conditions = str(
                    rule.get("Other Conditions", "")
                )

                rr.eligibility_source_url = str(
                    rule.get("eligibility_source_url", "")
                )

                rr.verification_status = str(
                    rule.get("verification_status", "needs_review")
                )

                rr.verified_eligibility_criteria = json_safe(
                    rule.get("verified_eligibility_criteria", [])
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ---------- Startup ----------

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    migrate_database()
    import_dataset()


# ---------- Home ----------

@app.get("/")
def home():
    return {
        "message": "SchemeMatch Backend is running!",
        "database": "PostgreSQL connected"
    }


# ---------- All Schemes ----------

@app.get("/schemes")
def get_schemes():
    db = SessionLocal()

    try:
        rows = db.query(Scheme).order_by(Scheme.scheme_id).all()
        rules = {
            r.scheme_id: r
            for r in db.query(EligibilityRule).all()
        }

        results = []

        for s in rows:
            r = rules.get(s.scheme_id)

            results.append({
                "scheme_id": s.scheme_id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "benefits": s.benefits,
                "eligibility": s.eligibility,
                "documents_required": s.documents_required,
                "application_process": s.application_process,
                "faqs": s.faqs,
                "official_url": s.official_url or s.official_source_url,
                "official_source_url": s.official_source_url,
                "eligibility_source_url": r.eligibility_source_url if r else "",
                "verification_status": r.verification_status if r else "needs_review",
                "verified_eligibility_criteria": r.verified_eligibility_criteria if r else []
            })

        return results

    finally:
        db.close()


# ---------- Eligibility Matching Helpers ----------

def occupation_relevant(profile_occupation: str, eligible_occupation: str) -> bool:
    rule = (eligible_occupation or "").lower()
    occ = (profile_occupation or "").lower().strip()

    if not rule or "all occupations" in rule or "any occupation" in rule or rule.strip() == "any":
        return True

    aliases = {
        "farmer": ["farmer", "agricultur", "cultivator", "grower", "landholding"],
        "student": ["student", "school", "college", "education", "scholarship"],
        "self-employed": ["self-employed", "entrepreneur", "business", "vendor", "artisan"],
        "woman": ["woman", "women", "female"],
    }

    terms = aliases.get(occ, [occ])
    return any(term in rule for term in terms)


def _number_in_rupees(value: str) -> Optional[float]:
    value = (value or "").lower().replace(",", "").replace("₹", "").strip()

    if not value:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|lakhs|thousand)?",
        value
    )

    if not match:
        return None

    amount = float(match.group(1))
    unit = (match.group(2) or "").strip()

    if unit in ("crore", "cr"):
        amount *= 10_000_000
    elif unit in ("lakh", "lac", "lakhs"):
        amount *= 100_000
    elif unit == "thousand":
        amount *= 1_000

    return amount


def _age_value(value: str) -> Optional[float]:
    value = (value or "").lower().strip()

    if not value or "no upper age" in value or "no age limit" in value:
        return None

    if any(word in value for word in ("deceased", "rpl", "depending", "either")):
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*years?(?:\s*(\d+)\s*months?)?",
        value
    )

    if not match:
        match = re.search(r"(\d+(?:\.\d+)?)", value)

    if not match:
        return None

    return float(match.group(1)) + int(match.group(2) or 0) / 12


def _occupation_match(profile_occupation: str, rule: str) -> Optional[bool]:
    rule = (rule or "").lower()

    if not rule:
        return None

    if "all occupations" in rule or "any occupation" in rule or rule.strip() == "any":
        return True

    return occupation_relevant(profile_occupation, rule)


def _location_match(profile_state: str, rule: str) -> Optional[bool]:
    rule = (rule or "").lower()

    if not rule:
        return None

    if "india" in rule and not any(term in rule for term in (
        "coffee-growing", "notified area", "rural areas",
        "urban areas", "rural india", "urban india"
    )):
        return True

    if profile_state and profile_state.lower() in rule:
        return True

    return None


# ---------- Eligibility Evaluation ----------

def _evaluate_scheme(profile: UserProfile, scheme: Scheme, rule: Optional[EligibilityRule]):
    matched = []
    unmet = []
    missing = []

    if rule is None:
        missing.append("No structured eligibility-rule record was found.")
        occupation_rule = minimum_age = maximum_age = income_rule = location_rule = ""
        other_conditions = scheme.eligibility or ""
    else:
        occupation_rule = rule.eligible_occupation or ""
        minimum_age = rule.minimum_age or ""
        maximum_age = rule.maximum_age or ""
        income_rule = rule.maximum_annual_income or ""
        location_rule = rule.eligible_location or ""
        other_conditions = rule.other_conditions or ""

    occ_result = _occupation_match(profile.occupation, occupation_rule)

    if occ_result is True:
        matched.append(f"Occupation matches: {occupation_rule}")
    elif occ_result is False:
        unmet.append(f"Occupation does not match: {occupation_rule}")
    else:
        missing.append("Occupation eligibility is not clearly specified.")

    min_text = minimum_age.lower()

    if "senior-citizen eligibility category" in min_text and profile.age < 70:
        missing.append("Other family eligibility needs verification.")
    elif "deceased breadwinner" in min_text:
        missing.append("Verify the deceased breadwinner's age.")
    elif "rpl" in min_text:
        missing.append("Minimum age depends on the RPL route.")
    else:
        min_age = _age_value(minimum_age)

        if min_age is not None:
            ok = profile.age > min_age if ("above" in min_text or "over" in min_text) else profile.age >= min_age
            (matched if ok else unmet).append(
                f"Age {'meets' if ok else 'does not meet'} minimum age ({minimum_age})."
            )

    max_text = maximum_age.lower()
    max_age = _age_value(maximum_age)

    if max_age is not None:
        ok = profile.age < max_age if ("below" in max_text or "under" in max_text) else profile.age <= max_age
        (matched if ok else unmet).append(
            f"Age {'meets' if ok else 'exceeds'} maximum age ({maximum_age})."
        )
    elif maximum_age and "no upper age" not in max_text and "no age limit" not in max_text:
        missing.append(f"Could not interpret maximum-age rule: {maximum_age}")

    if income_rule:
        inc_text = income_rule.lower()

        no_limit = any(t in inc_text for t in (
            "no income limit", "no fixed income limit",
            "no fixed annual income limit", "no general income limit",
            "no fixed national income limit"
        ))

        ambiguous = any(t in inc_text for t in (
            "family income", "monthly income", "alternative",
            "component", "bpl"
        ))

        if no_limit and not ambiguous:
            matched.append(f"Income rule: {income_rule}")
        elif ambiguous:
            missing.append(f"Income rule needs additional context: {income_rule}")
        else:
            limit = _number_in_rupees(income_rule)

            if limit is None:
                missing.append(f"Could not interpret income rule: {income_rule}")
            else:
                ok = profile.income <= limit
                (matched if ok else unmet).append(
                    f"Income {'is within' if ok else 'exceeds'} limit ({income_rule})."
                )
    else:
        missing.append("Income eligibility is not specified.")

    loc_result = _location_match(profile.state, location_rule)

    if loc_result is True:
        matched.append(f"Location matches: {location_rule}")
    else:
        missing.append(
            f"Location needs verification: {location_rule or 'No location rule supplied.'}"
        )

    if other_conditions:
        missing.append(
            f"Additional scheme-specific conditions need verification: {other_conditions}"
        )

    other_lower = other_conditions.lower()

    if (
        "scheduled caste (sc)" in other_lower
        or "sc students" in other_lower
        or "belonging to the sc category" in other_lower
    ):
        if profile.category.strip().lower() not in ("sc", "scheduled caste"):
            unmet.append("Applicant category does not meet the SC requirement.")

    if unmet:
        eligible, status = False, "Not eligible"
    elif missing:
        eligible, status = None, "Needs more information"
    else:
        eligible, status = True, "Eligible"

    return {
        "scheme_id": scheme.scheme_id,
        "scheme": scheme.name,
        "category": scheme.category,
        "eligible": eligible,
        "status": status,
        "matched_conditions": matched,
        "unmet_conditions": unmet,
        "missing_information": missing,
        "age_rule": minimum_age,
        "maximum_age_rule": maximum_age,
        "income_rule": income_rule,
        "occupation_rule": occupation_rule,
        "location_rule": location_rule,
        "other_conditions": other_conditions,
        "benefit": scheme.benefits,
        "description": scheme.description,
        "eligibility": scheme.eligibility,
        "documents_required": scheme.documents_required,
        "application_process": scheme.application_process,
        "official_url": scheme.official_url or scheme.official_source_url,
        "official_source_url": scheme.official_source_url,
        "eligibility_source_url": rule.eligibility_source_url if rule else "",
        "verification_status": rule.verification_status if rule else "needs_review",
        "verified_eligibility_criteria": rule.verified_eligibility_criteria if rule else []
    }


# ---------- Recommendation API ----------

@app.post("/recommend")
def recommend(profile: UserProfile):
    db = SessionLocal()

    try:
        rows = db.query(Scheme).order_by(Scheme.scheme_id).all()

        rule_rows = {
            r.scheme_id: r
            for r in db.query(EligibilityRule).all()
        }

        results = []

        for scheme in rows:
            rule = rule_rows.get(scheme.scheme_id)
            occupation = rule.eligible_occupation if rule else ""

            if not occupation_relevant(profile.occupation, occupation):
                continue

            results.append(_evaluate_scheme(profile, scheme, rule))

        return {
            "status": "success",
            "total_schemes": len(results),
            "recommendations": results
        }

    finally:
        db.close()


# ---------- AI Explanation API ----------

@app.post("/explain")
def explain(profile: UserProfile):
    db = SessionLocal()

    try:
        all_schemes = db.query(Scheme).all()

        rules = {
            r.scheme_id: r
            for r in db.query(EligibilityRule).all()
        }

        relevant = []

        for s in all_schemes:
            r = rules.get(s.scheme_id)

            if occupation_relevant(
                profile.occupation,
                r.eligible_occupation if r else ""
            ):
                relevant.append({
                    "scheme_id": s.scheme_id,
                    "name": s.name,
                    "category": s.category,
                    "benefits": s.benefits,
                    "eligibility": s.eligibility,
                    "documents_required": s.documents_required,
                    "official_url": s.official_url or s.official_source_url,
                    "eligibility_source_url": r.eligibility_source_url if r else "",
                    "verification_status": r.verification_status if r else "needs_review",
                    "verified_eligibility_criteria": r.verified_eligibility_criteria if r else [],
                    "occupation_rule": r.eligible_occupation if r else "",
                    "income_rule": r.maximum_annual_income if r else "",
                    "location_rule": r.eligible_location if r else "",
                    "other_conditions": r.other_conditions if r else ""
                })

        if not gemini_client:
            return {
                "explanation": "AI explanation is unavailable because GEMINI_API_KEY is not configured.",
                "retrieved_schemes": relevant
            }

        prompt = f"""
You are SchemeMatch, an Indian government scheme information assistant.

User profile:
Age: {profile.age}
Income: ₹{profile.income}
Occupation: {profile.occupation}
State: {profile.state}
Category: {profile.category}
Gender: {profile.gender}

Use ONLY the retrieved records below.
Explain possible matches in simple language.
Do not claim confirmed eligibility.
Clearly mention that schemes marked needs_review have not yet been fully verified.
Do not invent facts.

Retrieved records:
{json.dumps(relevant, ensure_ascii=False)}
"""

        try:
            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            explanation = response.text or "AI explanation is temporarily unavailable."

        except Exception as e:
            msg = str(e)

            explanation = (
                "Gemini API request quota has been reached. Please try again after the quota resets."
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg
                else "AI explanation is temporarily unavailable. Please try again later."
            )

        return {
            "explanation": explanation,
            "retrieved_schemes": relevant
        }

    finally:
        db.close()
