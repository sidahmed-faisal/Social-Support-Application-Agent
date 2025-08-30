# data_syntethizer.py
# -----------------------------------------
# Synthetic data generator aligned with UAE context:
# - Income: log-normal 3k–60k (median ~14k–15k)
# - Credit score: 300–900 (center ~650)
# - Assets/Liabilities -> realistic net worth (can be negative)
# - Emirates ID number: 784-YYYY-XXXXXXX-D (synthetic check digit)
# - Emirates ID image: PNG card via Pillow
#
# Produces (under synthetic_data/*):
#   bank_statements/*.csv
#   assets_liabilities/*.xlsx
#   credit_reports/*.json
#   emirates_ids/*.png
#   training/training_features.csv
#
# Usage:
#   python data_syntethizer.py
#   (or import and call generate_training_set(n=1000))

import os
import json
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Pillow for ID image
from PIL import Image, ImageDraw, ImageFont

try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None  # fallback if Faker isn't installed

# ---- Global RNG for reproducibility ----
rng = np.random.default_rng(42)

# ---------- File/Folder Helpers ----------
BASE_DIR = "synthetic_data"
FOLDERS = {
    "bank": os.path.join(BASE_DIR, "bank_statements"),
    "assets": os.path.join(BASE_DIR, "assets_liabilities"),
    "credit": os.path.join(BASE_DIR, "credit_reports"),
    "emirates_ids": os.path.join(BASE_DIR, "emirates_ids"),
    "testing": os.path.join(BASE_DIR, "test_data"),
}

def ensure_dirs():
    os.makedirs(BASE_DIR, exist_ok=True)
    for p in FOLDERS.values():
        os.makedirs(p, exist_ok=True)

BANKS = ['Emirates NBD', 'ADCB', 'FAB', 'ENBD', 'CBD']

# ---------- Simple Fakery Fallbacks ----------
def _fake_name():
    if fake:
        return fake.name()
    first = random.choice(["Ali", "Fatima", "Omar", "Huda", "Rashid", "Maryam"])
    last = random.choice(["Khan", "Hassan", "Abdullah", "Yousef", "Farooq", "Rahman"])
    return f"{first} {last}"

def _fake_address():
    if fake:
        return fake.address().replace("\n", ", ")
    return "Dubai, UAE"

def _fake_phone():
    if fake:
        return fake.phone_number()
    return f"+9715{random.randint(0,9)}{random.randint(1000000,9999999)}"

def _fake_email(name):
    if fake:
        return fake.email()
    base = name.lower().replace(" ", ".")
    return f"{base}@example.ae"

# ---------- Emirates ID number helpers ----------
def _luhn_like_check_digit(num_str: str) -> int:
    """Simple mod-10 check digit (Luhn-like) for synthetic realism."""
    s = 0
    alt = False
    for ch in reversed(num_str):
        d = ord(ch) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return (10 - (s % 10)) % 10

def generate_emirates_id(dob_year: int) -> str:
    """
    Synthetic Emirates ID pattern:
      784-YYYY-XXXXXXX-D
    - 784: UAE issuer code
    - YYYY: birth year
    - XXXXXXX: random 7 digits
    - D: simple check digit
    """
    issuer = "784"
    yyyy = f"{dob_year:04d}"
    serial = f"{rng.integers(0, 10**7):07d}"
    base = issuer + yyyy + serial
    check = _luhn_like_check_digit(base)
    return f"{issuer}-{yyyy}-{serial}-{check}"

# ---------- Emirates ID IMAGE ----------
def generate_emirates_id_image(profile):
    """Generate synthetic Emirates ID image"""
    img = Image.new('RGB', (1000, 750), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a common font, fallback to default
    try:
        for fname in ["arial.ttf", "DejaVuSans.ttf"]:
            try:
                font = ImageFont.truetype(fname, 30)
                break
            except Exception:
                font = None
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Add ID information
    draw.text((20, 20), "UNITED ARAB EMIRATES", fill='black', font=font)
    draw.text((20, 50), f"Name: {profile['name']}", fill='black', font=font)
    draw.text((20, 80), f"ID: {profile['emirates_id']}", fill='black', font=font)
    draw.text((20, 110), f"DOB: {profile['date_of_birth']}", fill='black', font=font)
    draw.text((20, 140), f"Nationality: {profile['nationality']}", fill='black', font=font)
    draw.text((20, 170), f"Gender: {profile['gender']}", fill='black', font=font)
    draw.text((20, 200), f"Employment: {profile['employment_status']}", fill='black', font=font)
    draw.text((20, 230), f"Marital: {profile['marital_status']}", fill='black', font=font)
    draw.text((20, 260), f"Disability: {profile['has_disability']}", fill='black', font=font)

    address_variant = profile['variants'].get('address', profile['address'])
    snippet = (address_variant[:40] + '...') if len(address_variant) > 43 else address_variant
    draw.text((20, 290), f"Address: {snippet}", fill='black', font=font)

    img_path = os.path.join(FOLDERS["emirates_ids"], f"{profile['name'].replace(' ', '_')}_emirates_id.png")
    img.save(img_path)

    return img_path

# ---------- Generators ----------
def generate_applicant_profile():
    """Generate a consistent applicant profile (UAE context, realistic ranges)"""
    monthly_income = int(np.clip(
        rng.lognormal(mean=np.log(14000), sigma=0.55), 3000, 60000
    ))

    employment_status = rng.choice(
        ['Employed', 'Unemployed', 'Self-employed'],
        p=[0.75, 0.12, 0.13]
    )

    housing_type = rng.choice(
        ['Owned', 'Rented', 'Shared'],
        p=[0.35, 0.55, 0.1]
    )

    monthly_rent = int(rng.integers(3500, 12001)) if housing_type == 'Rented' else 0

    name = _fake_name()
    address = _fake_address()
    phone = _fake_phone()
    email = _fake_email(name)

    dob = (datetime.now() - timedelta(days=int(rng.integers(18*365, 65*365)))).date()
    emirates_id = generate_emirates_id(dob.year)


    primary_bank = random.choice(BANKS)
    

    profile = {
        'id': str(rng.integers(10**12, 10**13)),
        'name': name,
        'emirates_id': emirates_id,
        'date_of_birth': dob,
        'nationality': rng.choice(['UAE', 'Indian', 'Pakistani', 'Egyptian', 'Filipino', 'Other'],
                                  p=[0.20, 0.28, 0.16, 0.12, 0.14, 0.10]),
        'gender': random.choice(['Male', 'Female']),
        'marital_status': rng.choice(['Single', 'Married', 'Divorced'],
                                     p=[0.40, 0.50, 0.1]),
        'address': address,
        'phone': phone,
        'email': email,
        'education': random.choice(['High School', 'Bachelor', 'Master', 'PhD', 'Diploma']),
        'employment_status': employment_status,
        'monthly_income': monthly_income,
        'family_size': int(rng.integers(1, 9)),
        'children_count': int(rng.integers(0, 6)),
        'has_disability': bool(rng.choice([True, False], p=[0.06, 0.94])),
        'housing_type': housing_type,
        'monthly_rent': monthly_rent,
        'primary_bank': primary_bank, 
    }

    # Inconsistency/noise variants
    profile_variants = {}
    for field in ['name', 'address', 'phone', 'monthly_income']:
        if random.random() < 0.2:
            if field == 'name':
                profile_variants[field] = (profile[field].replace(' ', '-') if random.choice([True, False])
                                           else profile[field].upper())
            elif field == 'address':
                profile_variants[field] = profile[field] + ', UAE'
            elif field == 'phone':
                profile_variants[field] = '+971' + profile[field][-9:]
            elif field == 'monthly_income':
                profile_variants[field] = profile[field] + random.randint(-500, 500)
        else:
            profile_variants[field] = profile[field]
    profile['variants'] = profile_variants

    # create Emirates ID image
    ensure_dirs()
    profile['emirates_id_image_path'] = generate_emirates_id_image(profile)

    return profile

# --- (bank statement, assets/liabilities, credit report functions unchanged) ---
def generate_bank_statement(profile):
    """Generate synthetic bank statement (UAE ranges) with bank_name as a CSV column on every row."""
    transactions = []
    base = max(500, int(0.5 * profile['variants'].get('monthly_income', profile['monthly_income'])))
    balance = base + int(rng.integers(1000, 40001))

    # ensure we have a consistent bank for this applicant
    bank_name = profile.get('primary_bank') or random.choice(BANKS)
    profile['primary_bank'] = bank_name  # persist for reuse in credit report

    for i in range(30):
        date = datetime.now() - timedelta(days=i)

        if i == 0 and profile['employment_status'] in ['Employed', 'Self-employed']:
            amount = int(profile['variants'].get('monthly_income', profile['monthly_income']))
            transactions.append({
                'date': date.strftime('%Y-%m-%d'),
                'description': 'SALARY CREDIT',
                'amount': amount,
                'balance': balance + amount,
                'type': 'Credit'
            })
            balance += amount

        if random.random() < 0.4:
            expense_type = random.choice(['GROCERY', 'UTILITIES', 'RENT', 'FUEL', 'SHOPPING', 'RESTAURANT'])
            amount = random.randint(50, 1500)
            if expense_type == 'RENT' and profile['housing_type'] == 'Rented':
                amount = profile['monthly_rent']

            transactions.append({
                'date': date.strftime('%Y-%m-%d'),
                'description': expense_type,
                'amount': -amount,
                'balance': balance - amount,
                'type': 'Debit'
            })
            balance -= amount

    # Build DataFrame and append identity + bank columns
    df = pd.DataFrame(transactions, columns=['date', 'description', 'amount', 'balance', 'type'])
    df['applicant_name'] = profile['name']
    df['emirates_id'] = profile['emirates_id']
    df['bank_name'] = bank_name  # <-- new column on every row

    csv_path = os.path.join(FOLDERS["bank"], f"{profile['name'].replace(' ', '_')}_bank_statement.csv")
    df.to_csv(csv_path, index=False)

    return {
        'applicant_name': profile['name'],
        'emirates_id': profile['emirates_id'],
        'account_holder': profile['variants'].get('name', profile['name']),
        'account_number': f"AE{random.randint(10**19, 10**20 - 1)}",
        'bank_name': bank_name,
        'average_balance': float(df['balance'].mean()) if not df.empty else balance,
        'total_credits': float(df.loc[df['amount'] > 0, 'amount'].sum()) if not df.empty else 0.0,
        'total_debits': float(-df.loc[df['amount'] < 0, 'amount'].sum()) if not df.empty else 0.0,
        'file_path': csv_path
    }


def generate_assets_liabilities(profile):
    """Generate assets and liabilities Excel and include applicant_name + emirates_id as columns in both sheets."""
    assets = []
    if profile['housing_type'] == 'Owned':
        assets.append({
            'Asset Type': 'Real Estate',
            'Description': 'Primary Residence',
            'Value (AED)': int(rng.integers(600_000, 2_500_001))
        })

    for asset_type in ['Bank Savings', 'Investments', 'Vehicle', 'Jewelry', 'Business']:
        if random.random() < 0.35:
            if asset_type == 'Business':
                value = int(rng.integers(80_000, 700_001))
            elif asset_type == 'Vehicle':
                value = int(rng.integers(30_000, 250_001))
            elif asset_type == 'Investments':
                value = int(rng.integers(20_000, 400_001))
            elif asset_type == 'Bank Savings':
                value = int(rng.integers(5_000, 300_001))
            else:
                value = int(rng.integers(5_000, 120_001))
            assets.append({
                'Asset Type': asset_type,
                'Description': f'{asset_type} holdings',
                'Value (AED)': value
            })

    liabilities = []
    if profile['housing_type'] == 'Owned' and random.random() < 0.7:
        liabilities.append({
            'Liability Type': 'Mortgage',
            'Description': 'Home Loan',
            'Amount (AED)': int(rng.integers(200_000, 1_800_001))
        })
    for liability_type in ['Credit Card', 'Personal Loan', 'Car Loan']:
        if random.random() < 0.45:
            if liability_type == 'Credit Card':
                amount = int(rng.integers(5_000, 80_001))
            elif liability_type == 'Car Loan':
                amount = int(rng.integers(30_000, 250_001))
            else:
                amount = int(rng.integers(20_000, 300_001))
            liabilities.append({
                'Liability Type': liability_type,
                'Description': f'{liability_type} debt',
                'Amount (AED)': amount
            })

    # Build DataFrames and add identity columns
    df_assets = pd.DataFrame(assets, columns=['Asset Type', 'Description', 'Value (AED)'])
    df_liabs  = pd.DataFrame(liabilities, columns=['Liability Type', 'Description', 'Amount (AED)'])

    # Include applicant identity columns on every row
    for df in (df_assets, df_liabs):
        if df.empty:
            # if a sheet is empty, keep headers + add the identity columns
            df['applicant_name'] = []
            df['emirates_id'] = []
        else:
            df['applicant_name'] = profile['name']
            df['emirates_id'] = profile['emirates_id']

    excel_path = os.path.join(FOLDERS["assets"], f"{profile['name'].replace(' ', '_')}_assets_liabilities.xlsx")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_assets.to_excel(writer, sheet_name='Assets', index=False)
        df_liabs.to_excel(writer, sheet_name='Liabilities', index=False)

    total_assets = int(df_assets['Value (AED)'].sum()) if not df_assets.empty else 0
    total_liabilities = int(df_liabs['Amount (AED)'].sum()) if not df_liabs.empty else 0

    return {
        'applicant_name': profile['name'],
        'emirates_id': profile['emirates_id'],
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': total_assets - total_liabilities,
        'file_path': excel_path
    }


# In the generate_credit_report function, add housing_type to the report
def generate_credit_report(profile):
    """Generate a single-account synthetic credit report as a PDF with consistent bank name."""
    credit_score = int(np.clip(rng.normal(loc=650, scale=90), 300, 900))

    # re-use the same bank as bank statement
    bank_name = profile.get('primary_bank') or random.choice(BANKS)
    profile['primary_bank'] = bank_name

    account = {
        'Account Type': random.choice(['Credit Card', 'Personal Loan', 'Auto Loan', 'Mortgage']),
        'Bank': bank_name,  # consistent
        'Credit Limit': int(rng.integers(10_000, 150_001)),
        'Outstanding Balance': int(rng.integers(0, 80_001)),
        'Payment History': random.choice(['Good', 'Fair', 'Poor']),
        'Account Status': random.choice(['Active', 'Closed', 'Delinquent'])
    }
    credit_accounts = [account]

    report = {
        'applicant_name': profile['name'],
        'emirates_id': profile['emirates_id'],
        'credit_score': credit_score,
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'total_credit_limit': account['Credit Limit'],
        'total_outstanding': account['Outstanding Balance'],
        'monthly_income_reported': profile['variants'].get('monthly_income', profile['monthly_income']),
        'housing_type': profile['housing_type'],  # ADD THIS LINE
        'credit_accounts': credit_accounts
    }

    pdf_path = os.path.join(FOLDERS["credit"], f"{profile['name'].replace(' ', '_')}_credit_report.pdf")

    # Try ReportLab first
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, y, "Synthetic Credit Report (UAE)")
        y -= 10 * mm

        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Name: {report['applicant_name']}"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Emirates ID: {report['emirates_id']}"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Report Date: {report['report_date']}"); y -= 10 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Summary")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Primary Bank: {bank_name}"); y -= 6 * mm  # <-- show bank in summary
        c.drawString(20 * mm, y, f"Credit Score: {report['credit_score']}"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Monthly Income (Reported): {report['monthly_income_reported']} AED"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Housing Type: {report['housing_type']}"); y -= 6 * mm  # ADD THIS LINE
        c.drawString(20 * mm, y, f"Total Credit Limit: {report['total_credit_limit']} AED"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Total Outstanding: {report['total_outstanding']} AED"); y -= 10 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Account")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Bank: {account['Bank']}"); y -= 6 * mm         # <-- bank in account section
        c.drawString(20 * mm, y, f"Type: {account['Account Type']}"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Credit Limit: {account['Credit Limit']} AED"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Outstanding Balance: {account['Outstanding Balance']} AED"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Payment History: {account['Payment History']}"); y -= 6 * mm
        c.drawString(20 * mm, y, f"Status: {account['Account Status']}"); y -= 10 * mm

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, y, "This document is auto-generated for testing and contains only synthetic data.")
        c.showPage()
        c.save()

    except Exception:
        # Fallback with Pillow (also shows bank name)
        img_w, img_h = (1240, 1754)
        img = Image.new('RGB', (img_w, img_h), color='white')
        draw = ImageDraw.Draw(img)
        try:
            font_hdr = ImageFont.truetype("DejaVuSans.ttf", 36)
            font = ImageFont.truetype("DejaVuSans.ttf", 22)
        except Exception:
            font_hdr = ImageFont.load_default()
            font = ImageFont.load_default()

        x, y = 60, 80
        draw.text((x, y), "Synthetic Credit Report (UAE)", fill='black', font=font_hdr); y += 70
        draw.text((x, y), f"Name: {report['applicant_name']}", fill='black', font=font); y += 35
        draw.text((x, y), f"Emirates ID: {report['emirates_id']}", fill='black', font=font); y += 35
        draw.text((x, y), f"Report Date: {report['report_date']}", fill='black', font=font); y += 50

        draw.text((x, y), f"Primary Bank: {bank_name}", fill='black', font=font); y += 35  # <-- summary bank
        draw.text((x, y), f"Credit Score: {report['credit_score']}", fill='black', font=font); y += 35
        draw.text((x, y), f"Monthly Income (Reported): {report['monthly_income_reported']} AED", fill='black', font=font); y += 35
        draw.text((x, y), f"Housing Type: {report['housing_type']}", fill='black', font=font); y += 35  # ADD THIS LINE
        draw.text((x, y), f"Total Credit Limit: {report['total_credit_limit']} AED", fill='black', font=font); y += 35
        draw.text((x, y), f"Total Outstanding: {report['total_outstanding']} AED", fill='black', font=font); y += 50

        draw.text((x, y), "Account", fill='black', font=font_hdr); y += 50
        draw.text((x, y), f"Bank: {account['Bank']}", fill='black', font=font); y += 35   # <-- account bank
        draw.text((x, y), f"Type: {account['Account Type']}", fill='black', font=font); y += 35
        draw.text((x, y), f"Credit Limit: {account['Credit Limit']} AED", fill='black', font=font); y += 35
        draw.text((x, y), f"Outstanding Balance: {account['Outstanding Balance']} AED", fill='black', font=font); y += 35
        draw.text((x, y), f"Payment History: {account['Payment History']}", fill='black', font=font); y += 35
        draw.text((x, y), f"Status: {account['Account Status']}", fill='black', font=font); y += 50

        draw.text((x, img_h - 100), "This document is auto-generated for testing and contains only synthetic data.", fill='black', font=font)
        img.save(pdf_path, "PDF", resolution=150.0)

    report['file_path'] = pdf_path
    return report

# ---------- High-level Bundling & Training CSV ----------
def synthesize_applicant_bundle():
    profile = generate_applicant_profile()
    bank = generate_bank_statement(profile)
    assets_liabs = generate_assets_liabilities(profile)
    credit = generate_credit_report(profile)

    row = {
        "monthly_income": int(profile['variants'].get('monthly_income', profile['monthly_income'])),
        "family_size": int(profile['family_size']),
        "employment_status": str(profile['employment_status']),
        "housing_type": str(profile['housing_type']),
        "marital_status": str(profile['marital_status']),
        "has_disability": bool(profile['has_disability']),
        "nationality": str(profile['nationality']),
        "credit_score": int(credit['credit_score']),
        "net_worth": int(assets_liabs['net_worth']),

    }
    return row

def generate_test_set(n=500, output_csv=None):
    ensure_dirs()
    rows = [synthesize_applicant_bundle() for _ in range(n)]
    df = pd.DataFrame(rows)
    if output_csv is None:
        output_csv = os.path.join(FOLDERS["testing"], "test_set.csv")
    df.to_csv(output_csv, index=False)
    return output_csv, df

if __name__ == "__main__":
    ensure_dirs()
    out_path, df = generate_test_set(n=5)
    print(f"✅ Generated {len(df)} testing rows at: {out_path}")
    print(df.head(5))
