import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from eligibility_classifier import EligibilityClassifier

# Load and prepare synthetic data
def load_training_data():
    """Load and prepare balanced, UAE-context synthetic data"""
    import pandas as pd
    import numpy as np

    rng = np.random.default_rng(42)
    n_samples = 5000

    # --- Feature generation (UAE context) ---
    # Income: log-normal-ish with long tail; many around 8k–20k, some 20k–60k
    monthly_income = np.clip(rng.lognormal(mean=np.log(14000), sigma=0.55, size=n_samples), 3000, 60000).astype(int)

    family_size = rng.integers(1, 8, size=n_samples)
    employment_status = rng.choice(['Employed', 'Unemployed', 'Self-employed'], size=n_samples, p=[0.78, 0.12, 0.10])
    housing_type = rng.choice(['Owned', 'Rented', 'Shared'], size=n_samples, p=[0.35, 0.55, 0.10])
    marital_status = rng.choice(['Single', 'Married', 'Divorced'], size=n_samples, p=[0.40, 0.55, 0.05])
    has_disability = rng.choice([True, False], size=n_samples, p=[0.06, 0.94])
    nationality = rng.choice(['UAE', 'Indian', 'Pakistani', 'Egyptian', 'Filipino', 'Other'], size=n_samples,
                             p=[0.2, 0.28, 0.16, 0.12, 0.14, 0.10])

    # Credit scores in UAE: ~300–900; center around 650 with spread
    credit_score = np.clip(rng.normal(loc=650, scale=90, size=n_samples), 300, 900).astype(int)

    # Net worth (AED): allow negatives; wide spread with right tail
    net_worth = np.clip(rng.normal(loc=150000, scale=250000, size=n_samples), -300000, 1500000).astype(int)

    df = pd.DataFrame({
        'monthly_income': monthly_income,
        'family_size': family_size,
        'employment_status': employment_status,
        'housing_type': housing_type,
        'marital_status': marital_status,
        'has_disability': has_disability,
        'nationality': nationality,
        'credit_score': credit_score,
        'net_worth': net_worth
    })

    # --- Latent "financial hardship" score (noisy & non-linear) ---
    # Lower income, lower net worth, larger family, unemployment, disability increase hardship
    # Higher credit score, owned housing, marriage (dual income proxy) decrease hardship (loosely)
    emp_penalty = np.where(df['employment_status'] == 'Unemployed', 1.0,
                   np.where(df['employment_status'] == 'Self-employed', 0.25, 0.0))
    house_bonus = np.where(df['housing_type'] == 'Owned', -0.25,
                   np.where(df['housing_type'] == 'Shared', 0.25, 0.0))
    marital_bonus = np.where(df['marital_status'] == 'Married', -0.1, 0.0)
    disability_penalty = np.where(df['has_disability'], 0.7, 0.0)

    # Scale continuous terms to comparable ranges
    inc_term = (15000 - df['monthly_income']) / 15000.0        # <0 if income > 15k
    nw_term  = (100000 - df['net_worth']) / 100000.0           # <0 if net worth > 100k
    cs_term  = (650 - df['credit_score']) / 150.0              # <0 if score > 650
    fam_term = (df['family_size'] - 3) / 2.0                   # >0 for larger families

    # Non-linearity: people far above 40k income or >800k net worth get diminishing hardship anyway
    inc_nl = -0.6 * (df['monthly_income'] > 40000).astype(float)
    nw_nl  = -0.6 * (df['net_worth'] > 800000).astype(float)

    noise = rng.normal(0, 0.35, size=n_samples)

    latent = (
        1.4*inc_term + 1.0*nw_term + 0.9*cs_term + 0.6*fam_term
        + emp_penalty + disability_penalty + house_bonus + marital_bonus
        + inc_nl + nw_nl + noise
    )

    # --- Balanced labels: threshold at the median of latent ---
    thresh = np.median(latent)
    eligible = (latent > thresh).astype(int)

    df['eligible'] = eligible

    # Return features and target
    return df.drop(columns=['eligible']), df['eligible']


def main():
    print("Loading training data...")
    X, y = load_training_data()
    
    print("Splitting data into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training eligibility classifier...")
    classifier = EligibilityClassifier()
    classifier.fit(X_train, y_train)
    
    print("Evaluating model...")
    train_score = classifier.model.score(
        classifier.preprocess_data(X_train), 
        y_train
    )
    test_score = classifier.model.score(
        classifier.preprocess_data(X_test), 
        y_test
    )
    
    print(f"Train accuracy: {train_score:.4f}")
    print(f"Test accuracy: {test_score:.4f}")
    
    print("Saving model...")
    classifier.save('eligibility_model.pkl')
    print("Model saved successfully!")

if __name__ == "__main__":
    main()