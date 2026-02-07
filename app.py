# ============================== APP ENTRY POINT ============================= #

"""
Jason Fitness Tracker — Dash application entry point.

Run locally:
    python app.py

Production (Render / Heroku):
    gunicorn app:server
"""

import os

from dash import dash

from src.layouts import create_layout
from src.callbacks import register_callbacks

# ------------------------------ Initialise App ------------------------------ #

app = dash.Dash(__name__, assets_folder="assets")
server = app.server

# ------------------------------ Layout & Callbacks -------------------------- #

app.layout = create_layout()
register_callbacks(app)

# ------------------------------ Run ----------------------------------------- #

current_file = os.path.basename(__file__)
print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == "__main__":
    print('=' * 40)
    print(f"Starting Jason Fitness Tracker app!")
    print('=' * 40)

    app.run(debug=True)
