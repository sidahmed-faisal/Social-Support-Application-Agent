import pandas as pd
from eligibility_classifier import EligibilityClassifier

# Load trained model
clf = EligibilityClassifier.load("eligibility_model.pkl")

# Example applicants
test_data = pd.DataFrame([
    {
        "monthly_income": 7000,
        "family_size": 5,
        "employment_status": "Employed",
        "housing_type": "Rented",
        "marital_status": "Married",
        "has_disability": False,
        "nationality": "Filipino",
        "credit_score": 400,
        "net_worth": 20000
    },
    {
        "monthly_income": 17147,
        "family_size": 4,
        "employment_status": "Employed",
        "housing_type": "Rented",
        "marital_status": "Married",
        "has_disability": False,
        "nationality": "Indian",
        "credit_score": 682,
        "net_worth": 30125
    },
    {
        "monthly_income": 9430,
        "family_size": 2,
        "employment_status": "Employed",
        "housing_type": "Owned",
        "marital_status": "Married",
        "has_disability": False,
        "nationality": "Indian",
        "credit_score": 590,
        "net_worth": 2031264
    },
    {
        "monthly_income": 10000,
        "family_size": 7,
        "employment_status": "Unemployed",
        "housing_type": "Rented",
        "marital_status": "Married",
        "has_disability": False,
        "nationality": "UAE",
        "credit_score": 592,
        "net_worth": 46646
    },
    {
        "monthly_income": 31857,
        "family_size": 1,
        "employment_status": "Employed",
        "housing_type": "Rented",
        "marital_status": "Married",
        "has_disability": False,
        "nationality": "Pakistani",
        "credit_score": 632,
        "net_worth": -405455
    },
])
preds = clf.predict(test_data)              # 0/1
probs = clf.predict_proba(test_data)[:, 1]  # probability of being eligible
print(preds)
print(probs)
