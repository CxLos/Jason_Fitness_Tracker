# =================================== CONFIG ================================= #

"""
Application configuration, constants, and credential management.
"""

import os
import json
import base64
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ================================= Constants ================================ #

APP_NAME = "Jason"
REPORT_MONTH = datetime(2026, 1, 1).strftime("%B")
REPORT_YEAR = datetime(2026, 1, 1).strftime("%Y")

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1M8cbhrw-r8ddd_2_SWIvsuAaBL-Jt2L2s-D2mo6T8Ss/"
    "edit?gid=1491449677#gid=1491449677"
)

YEAR_OPTIONS = [
    {"label": "All Time", "value": "All Time"},
]

COLUMNS = [
    "Timestamp", "Date", "Push Exercise", "Triceps Exercise",
    "Pull Exercise", "Leg Exercise", "Bicep Exercise",
    "Shoulder Exercise", "Forearm Exercise", "Abs Exercise",
    "Calisthenics Exercise", "Cardio Exercise", "Weight",
    "Set 1", "Set 2", "Set 3", "Set 4", "Set 5",
    "Time", "Distance", "Floors", "Calories",
]

# Muscle group definitions: (exercise_column, label, weight_cols)
WEIGHT_GROUPS = [
    ("Push Exercise", "Push"),
    ("Triceps Exercise", "Tricep"),
    ("Pull Exercise", "Pull"),
    ("Leg Exercise", "Leg"),
    ("Bicep Exercise", "Bicep"),
    ("Shoulder Exercise", "Shoulder"),
    ("Forearm Exercise", "Forearm"),
    ("Abs Exercise", "Ab"),
    ("Calisthenics Exercise", "Calisthenics"),
]

WEIGHT_COLS = ["Date", "Weight", "Set 1", "Set 2", "Set 3", "Set 4", "Set 5"]
CARDIO_COLS = ["Date", "Time", "Distance", "Floors", "Calories"]

CARDIO_METRIC_MAP = {
    "Bike": ("Distance", "Miles"),
    "Indoor Run": ("Distance", "Miles"),
    "Outdoor Run": ("Distance", "Miles"),
    "Stair Master": ("Floors", "Floors"),
    "Jump Rope": ("Time", "Min"),
}

# ================================ Credentials =============================== #

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_gspread_client() -> gspread.Client:
    """Authenticate and return a gspread client."""
    encoded_key = os.getenv("GOOGLE_CREDENTIALS")

    if encoded_key:
        # Render / production: base64-encoded JSON env var
        json_key = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
        creds = Credentials.from_service_account_info(json_key, scopes=SCOPE)
    else:
        # Local development fallback
        creds_path = (
            r"C:\Users\CxLos\OneDrive\Documents\Portfolio Projects"
            r"\GCP\personal-projects-485203-6f6c61641541.json"
        )
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                "Service account JSON not found and GOOGLE_CREDENTIALS is not set."
            )
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPE)

    return gspread.authorize(creds)


# Initialise a shared client & sheet reference at import time
client = get_gspread_client()
sheet = client.open_by_url(SHEET_URL)
