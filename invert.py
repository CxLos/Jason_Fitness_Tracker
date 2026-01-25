# =================================== IMPORTS ================================= #

import numpy as np 
import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns 
from datetime import datetime
import os
import sys
# -------------------------------
import requests
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
# --------------------------------
import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.development.base_component import Component

# 'data/~$bmhc_data_2024_cleaned.xlsx'
# print('System Version:', sys.version)

# -------------------------------------- DATA ------------------------------------------- #

current_dir = os.getcwd()
current_file = os.path.basename(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
# print("Current Directory: \n", os.getcwd()) 

report_month = datetime(2026, 1, 1).strftime("%B")
report_year = datetime(2026, 1, 1).strftime("%Y")

# Define the Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1EXDabqzS1Gd1AteSqcovvUuJxrUMQvisf_MhnhFMeNk/edit?gid=0#gid=0"

# Define the scope
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load credentials
encoded_key = os.getenv("GOOGLE_CREDENTIALS")

if encoded_key:
    # Render: GOOGLE_CREDENTIALS is BASE64 ENCODED JSON
    json_key = json.loads(
        base64.b64decode(encoded_key).decode("utf-8")
    )
    creds = Credentials.from_service_account_info(json_key, scopes=scope)

else:
    # Local development fallback
    creds_path = r"C:\Users\CxLos\OneDrive\Documents\Portfolio Projects\GCP\personal-projects-485203-6f6c61641541.json"

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            "Service account JSON file not found and GOOGLE_CREDENTIALS is not set."
        )

    creds = Credentials.from_service_account_file(creds_path, scopes=scope)

# Authorize and load the sheet
client = gspread.authorize(creds)
sheet = client.open_by_url(sheet_url)
worksheet = sheet.worksheet(f"{report_year}")
worksheet = sheet.worksheet("Jason")
data = pd.DataFrame(worksheet.get_all_records())
raw_data = worksheet.get_all_records() 
# data = pd.DataFrame(raw_data)

# Debug: Print raw data from Google Sheets
# print("Raw data from gspread:")
# print(f"First row: {raw_data[0]}")
# print(f"Bench Press row: {[row for row in raw_data if 'Bench' in row.get('Exercise', '')][:1]}")

df = data.copy()

# print(df.head())

# Transpose the DataFrame (invert rows and columns)
df_indexed = df.set_index(pd.Index(range(1, len(df) + 1))) # Set custom 1-based index
df_indexed = df_indexed.T
df_indexed = df_indexed.reset_index()
df_indexed.columns = ['Field'] + [f'Row {i+1}' for i in range(len(df_indexed.columns)-1)]

# print(df_indexed.head())

# print to excel
# df_indexed.to_excel('transposed_fitness_data.xlsx', index=False)

# =================================== Updated Database ================================= #

updated_path1 = 'data/jason_data_transposed.xlsx'
data_path1 = os.path.join(script_dir, updated_path1)
df_indexed.to_excel(data_path1, index=False)
print(f"DataFrame saved to {data_path1}")

# updated_path = f'data/Admin_{report_month}_{report_year}.xlsx'
# data_path = os.path.join(script_dir, updated_path)

# with pd.ExcelWriter(data_path, engine='xlsxwriter') as writer:
#     df.to_excel(
#             writer, 
#             sheet_name=f'MarCom {report_month} {report_year}', 
#             startrow=1, 
#             index=False
#         )

#     # Create the workbook to access the sheet and make formatting changes:
#     workbook = writer.book
#     sheet1 = writer.sheets['MarCom April 2025']
    
#     # Define the header format
#     header_format = workbook.add_format({
#         'bold': True, 
#         'font_size': 13, 
#         'align': 'center', 
#         'valign': 'vcenter',
#         'border': 1, 
#         'font_color': 'black', 
#         'bg_color': '#B7B7B7',
#     })
    
#     # Set column A (Name) to be left-aligned, and B-E to be right-aligned
#     left_align_format = workbook.add_format({
#         'align': 'left',  # Left-align for column A
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })

#     right_align_format = workbook.add_format({
#         'align': 'right',  # Right-align for columns B-E
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })
    
#     # Create border around the entire table
#     border_format = workbook.add_format({
#         'border': 1,  # Add border to all sides
#         'border_color': 'black',  # Set border color to black
#         'align': 'center',  # Center-align text
#         'valign': 'vcenter',  # Vertically center text
#         'font_size': 12,  # Set font size
#         'font_color': 'black',  # Set font color to black
#         'bg_color': '#FFFFFF'  # Set background color to white
#     })

#     # Merge and format the first row (A1:E1) for each sheet
#     sheet1.merge_range('A1:Q1', f'MarCom Report {report_month} {report_year}', header_format)

#     # Set column alignment and width
#     # sheet1.set_column('A:A', 20, left_align_format)  

#     print(f"MarCom Excel file saved to {data_path}")
