
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="SchemeMatch API",
    description="Government Scheme Eligibility and Recommendation Engine"
)

# Allow the GitHub Pages website to access this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bhavisha-exe.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserProfile(BaseModel):
    age: int
    income: float
    occupation: str
    state: str
    category: str
    gender: str


schemes = [
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


@app.get("/")
def home():
    return {
        "message": "SchemeMatch Backend is running!"
    }


@app.post("/recommend")
def recommend(profile: UserProfile):
    results = []

    for scheme in schemes:
        matched = []
        unmet = []

        if (
            scheme["occupation"] == "Any"
            or scheme["occupation"].lower()
            == profile.occupation.lower()
        ):
            matched.append("Occupation condition matched")
        else:
            unmet.append("Occupation condition not matched")

        if profile.income <= scheme["max_income"]:
            matched.append("Income condition matched")
        else:
            unmet.append("Income condition not matched")

        eligible = len(unmet) == 0

        results.append({
            "scheme": scheme["name"],
            "eligible": eligible,
            "status": (
                "Eligible"
                if eligible
                else "Needs further checking"
            ),
            "matched_conditions": matched,
            "unmet_conditions": unmet,
            "benefit": scheme["benefit"]
        })

    return {
        "status": "success",
        "total_schemes": len(results),
        "recommendations": results
    }
