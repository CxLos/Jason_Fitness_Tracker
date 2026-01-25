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

# ============================== Data Loading Function ========================== #

def load_data_for_year(year):
    """Load and process fitness data for a specific year or all years"""
    if year == 'All Time':
        # Load and combine all years
        all_years = ['2024', '2025', '2026']
        dfs = []
        for yr in all_years:
            try:
                worksheet = sheet.worksheet(f"Jason_{yr}")
                data = pd.DataFrame(worksheet.get_all_records())
                dfs.append(data)
            except:
                # Skip if worksheet doesn't exist
                print(f"Worksheet {yr} not found, skipping...")
                continue
        
        if dfs:
            # Combine all dataframes
            combined_df = pd.concat(dfs, ignore_index=True)
            return combined_df.copy()
        else:
            # Return empty dataframe if no data found
            return pd.DataFrame()
    else:
        worksheet = sheet.worksheet(f"{year}")
        data = pd.DataFrame(worksheet.get_all_records())
        return data.copy()

# Load default year (All Time)
df = load_data_for_year('All Time')

# -------------------------------------------------
# print(df.head())
# print(df[["Date of Activity", "Total travel time (minutes):"]])
# print('Total Marketing Events: ', len(df))
# print('Column Names: \n', df.columns.tolist())
# print('DF Shape:', df.shape)
# print('Dtypes: \n', df.dtypes)
# print('Info:', df.info())
# print("Amount of duplicate rows:", df.duplicated().sum())
# print('Current Directory:', current_dir)
# print('Script Directory:', script_dir)
# print('Path to data:',file_path)

# ================================= Columns ================================= #

columns =  [

]

# =============================== Missing Values ============================ #

# missing = df.isnull().sum()
# print('Columns with missing values before fillna: \n', missing[missing > 0])

#  Please provide public information:    137
# Please explain event-oriented:        13

# ============================== Data Preprocessing ========================== #

# Check for duplicate columns
# duplicate_columns = df.columns[df.columns.duplicated()].tolist()
# print(f"Duplicate columns found: {duplicate_columns}")
# if duplicate_columns:
#     print(f"Duplicate columns found: {duplicate_columns}")

# Get all date columns (everything except Category and Exercise)
date_columns = [col for col in df.columns if col not in ['Category', 'Exercise']]

# Debug: See what columns are being melted
# print("All columns in df:", df.columns.tolist())
# print(f"\nDate columns to melt: {date_columns}")
# print(f"\nFirst few rows of df:", df.head())

# Reshape from wide to long format
df_long = df.melt(
    id_vars=['Category', 'Exercise'],  # columns to keep
    value_vars=date_columns,  # columns to melt into rows
    var_name='Date',        # New column name
    value_name='Weight'     # New column name for cell values
)

# Filter out invalid date strings before converting
# Remove rows where Date contains common non-date values
df_long = df_long[~df_long['Date'].astype(str).str.contains('Int\.|Unnamed|#', case=False, na=False)]

# Convert Date to datetime with format specification
df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce', format='mixed')

# Remove rows with invalid dates (NaT)
df_long = df_long.dropna(subset=['Date'])

# Sort by date
df_long = df_long.sort_values('Date')

# Convert Weight to numeric BEFORE creating charts
df_long['Weight'] = pd.to_numeric(df_long['Weight'], errors='coerce')

# Remove rows with NaN weights
df_long = df_long.dropna(subset=['Weight'])
df_long = df_long[df_long['Weight'].notna()]
df_long = df_long[df_long['Weight'] != '']  # Remove empty strings

# Strip whitespace from string columns and convert to string type explicitly
df_long['Category'] = df_long['Category'].astype(str).str.strip()
df_long['Exercise'] = df_long['Exercise'].astype(str).str.strip()

# Remove duplicate rows (same exercise on same date)
df_long = df_long.drop_duplicates(subset=['Category', 'Exercise', 'Date'], keep='first')

# Reset index to avoid grouping issues in Plotly
df_long = df_long.reset_index(drop=True)

# Ensure all columns have the correct explicit types for pandas 3.0 compatibility
df_long['Category'] = df_long['Category'].astype('object')
df_long['Exercise'] = df_long['Exercise'].astype('object')
df_long['Date'] = pd.to_datetime(df_long['Date'])
df_long['Weight'] = df_long['Weight'].astype('float64')

print("Melted DataFrame: \n", df_long.head(10))
# print("\nDataFrame dtypes:\n", df_long.dtypes)
# print("\nUnique exercises:\n", df_long['Exercise'].unique())

# Helper to build line charts without relying on Plotly Express grouping
def make_line_chart(df_cat: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()

    if df_cat.empty:
        fig.update_layout(title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20)))
        return fig

    for exercise_name, sub in df_cat.groupby('Exercise'):
        # print("exercise_name:", exercise_name)
        # print(sub.head(), "\n")
        sub_sorted = sub.sort_values('Date')
        fig.add_trace(
            go.Scatter(
                x=sub_sorted['Date'],
                y=sub_sorted['Weight'],
                mode='lines+markers',
                name=str(exercise_name),
                hovertemplate='Exercise: <b>%{fullData.name}</b><br>Date: <b>%{x|%m/%d/%Y}</b><br>Weight: <b>%{y} lbs.</b><extra></extra>',
            )
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20)),
        xaxis=dict(tickformat='%m/%d/%Y', title='Date'),
        yaxis=dict(title='Weight (lbs)'),
        hovermode='closest',
        font=dict(size=12),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    return fig

# =========================== Total Exercises =========================== #

total_gym_days = len(df)
# print("Total events:", total_exercises)

# ========================= Push Exercises =========================== #

# Filter for Push category and create explicit copy
df_push = df_long[df_long['Category'] == 'Push'].reset_index(drop=True)
# df_push = df_push.reset_index(drop=True)
# print("DF Push: \n", df_push.head())

df_push["Exercise"] = (
    df_push["Exercise"]
    .astype(str)
    .str.strip()
)

df_push = df_push.dropna(subset=["Exercise", "Date", "Weight"])

# print(f"\nPush exercises found: {len(df_push)}")
# print(f"Push exercise names: {df_push['Exercise'].unique()}")
push_line = make_line_chart(df_push, 'Push Progress Over Time')

# Create push pie chart data
df_push_counts = df_push['Exercise'].value_counts().reset_index()
df_push_counts.columns = ['Exercise', 'Count']

push_bar = px.bar(
    df_push_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Push Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        visible=False,
        # visible=True,
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

push_pie = px.pie(
    df_push_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Push Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    # textinfo='value+percent',
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Pull Exercises =========================== #

# Filter for Pull category and reset index
df_pull = df_long[df_long['Category'] == 'Pull'].reset_index(drop=True)

pull_line = make_line_chart(df_pull, 'Pull Progress Over Time')

# Create pull pie chart data
df_pull_counts = df_pull['Exercise'].value_counts().reset_index()
df_pull_counts.columns = ['Exercise', 'Count']

pull_bar = px.bar(
    df_pull_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Pull Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

pull_pie = px.pie(
    df_pull_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Pull Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Leg Exercises =========================== #

# Filter for Leg category and reset index
df_leg = df_long[df_long['Category'] == 'Leg'].reset_index(drop=True)

leg_line = make_line_chart(df_leg, 'Leg Progress Over Time')

# Create leg pie chart data
df_leg_counts = df_leg['Exercise'].value_counts().reset_index()
df_leg_counts.columns = ['Exercise', 'Count']

leg_bar = px.bar(
    df_leg_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Leg Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

leg_pie = px.pie(
    df_leg_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Leg Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Bicep Exercises =========================== #

# Filter for Bicep category and reset index
df_bicep = df_long[df_long['Category'] == 'Bicep'].reset_index(drop=True)

bicep_line = make_line_chart(df_bicep, 'Bicep Progress Over Time')

# Create bicep pie chart data
df_bicep_counts = df_bicep['Exercise'].value_counts().reset_index()
df_bicep_counts.columns = ['Exercise', 'Count']

bicep_bar = px.bar(
    df_bicep_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Bicep Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

bicep_pie = px.pie(
    df_bicep_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Bicep Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Tricep Exercises =========================== #

# Filter for Tricep category and reset index
df_tricep = df_long[df_long['Category'] == 'Tricep'].reset_index(drop=True)

tricep_line = make_line_chart(df_tricep, 'Tricep Progress Over Time')

# Create tricep pie chart data
df_tricep_counts = df_tricep['Exercise'].value_counts().reset_index()
df_tricep_counts.columns = ['Exercise', 'Count']

tricep_bar = px.bar(
    df_tricep_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Tricep Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

tricep_pie = px.pie(
    df_tricep_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Tricep Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Shoulder Exercises =========================== #

# Filter for Shoulder category and reset index
df_shoulder = df_long[df_long['Category'] == 'Shoulder'].reset_index(drop=True)

shoulder_line = make_line_chart(df_shoulder, 'Shoulder Progress Over Time')

# Create shoulder pie chart data
df_shoulder_counts = df_shoulder['Exercise'].value_counts().reset_index()
df_shoulder_counts.columns = ['Exercise', 'Count']

shoulder_bar = px.bar(
    df_shoulder_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Shoulder Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

shoulder_pie = px.pie(
    df_shoulder_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Shoulder Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Forearm Exercises =========================== #

# Filter for Forearm category and reset index
df_forearm = df_long[df_long['Category'] == 'Forearm'].reset_index(drop=True)

forearm_line = make_line_chart(df_forearm, 'Forearm Progress Over Time')

# Create forearm pie chart data
df_forearm_counts = df_forearm['Exercise'].value_counts().reset_index()
df_forearm_counts.columns = ['Exercise', 'Count']

forearm_bar = px.bar(
    df_forearm_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Forearm Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

forearm_pie = px.pie(
    df_forearm_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Forearm Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Ab Exercises =========================== #

# Filter for Ab category and reset index
df_ab = df_long[df_long['Category'] == 'Ab'].reset_index(drop=True)

ab_line = make_line_chart(df_ab, 'Ab Progress Over Time')

# Create ab pie chart data
df_ab_counts = df_ab['Exercise'].value_counts().reset_index()
df_ab_counts.columns = ['Exercise', 'Count']

ab_bar = px.bar(
    df_ab_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Ab Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

ab_pie = px.pie(
    df_ab_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Ab Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Calisthenics Exercises =========================== #

# Filter for Calisthenics category and reset index
df_calisthenics = df_long[df_long['Category'] == 'Calisthenics'].reset_index(drop=True)

calisthenics_line = make_line_chart(df_calisthenics, 'Calisthenics Progress Over Time')

# Create calisthenics pie chart data
df_calisthenics_counts = df_calisthenics['Exercise'].value_counts().reset_index()
df_calisthenics_counts.columns = ['Exercise', 'Count']

calisthenics_bar = px.bar(
    df_calisthenics_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Calisthenics Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

calisthenics_pie = px.pie(
    df_calisthenics_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Calisthenics Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================= Cardio Exercises =========================== #

# Filter for Cardio category and reset index
df_cardio = df_long[df_long['Category'] == 'Cardio'].reset_index(drop=True)

cardio_line = make_line_chart(df_cardio, 'Cardio Progress Over Time')

# Create cardio pie chart data
df_cardio_counts = df_cardio['Exercise'].value_counts().reset_index()
df_cardio_counts.columns = ['Exercise', 'Count']

cardio_bar = px.bar(
    df_cardio_counts,
    y="Exercise",
    x='Count',
    color="Exercise",
    text='Count',
    orientation='h'
).update_layout(
    title=dict(
        text=f'Cardio Exercise Bar Chart - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    yaxis=dict(
        tickfont=dict(size=16),  
        title=dict(
            text="Exercise",
            font=dict(size=16),  
        ),
    ),
    xaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=16),  
        ),
    ),
    legend=dict(
        title='Exercise',
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        visible=False,
    ),
    hovermode='closest',
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    textposition='auto',
    hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
)

cardio_pie = px.pie(
    df_cardio_counts,
    names="Exercise",
    values='Count'
).update_layout(
    title=dict(
        text=f'Cardio Exercise Distribution - {report_year}',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    texttemplate='%{percent:.1%}',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ========================== DataFrame Table ========================== #

# create a display index column and prepare table data/columns
# reset index to ensure contiguous numbering after any filtering/sorting upstream
df_indexed = df_long.reset_index(drop=True).copy()

# Reorder columns: Date first, then the rest
column_order = ['Date', 'Category', 'Exercise', 'Weight']
df_indexed = df_indexed[column_order]

# Insert '#' as the first column (1-based row numbers)
df_indexed.insert(0, '#', df_indexed.index + 1)

# Convert to records for DataTable
data = df_indexed.to_dict('records')
columns = [{"name": col, "id": col} for col in df_indexed.columns]

# ============================== Dash Application ========================== #

app = dash.Dash(__name__)
server= app.server

app.layout = html.Div(
    children=[ 
        html.Div(
            className='divv', 
            children=[ 
                html.H1(
                    f"Jason Fitness Tracker",  
                    className='title'),
                html.H1(
                    id='year-subtitle',
                    children='All Time',  
                    className='title2'),
                html.Div(
                    className='dropdown-container',
                    children=[
                        html.Label('', style={'marginRight': '10px', 'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='year-dropdown',
                            options=[
                                {'label': 'All Time', 'value': 'All Time'},
                                {'label': '2026', 'value': '2026'},
                            ],
                            value='All Time',
                            clearable=False,
                            style={
                                'width': '150px',
                                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Calibri, Arial, sans-serif',
                                'backgroundColor': 'rgb(253, 180, 180)',
                                'border': '2px solid rgb(217, 24, 24)',
                                'borderRadius': '50px'
                            }
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '20px 0'}
                ),
                html.Div(
                    className='btn-box', 
                    children=[
                        html.A(
                            'Repo',
                            href=f'https://github.com/CxLos/Jason_Fitness_Tracker',
                            className='btn'
                        ),
                    ]
                ),
            ]
        ),  

# ============================ Rollups ========================== #

html.Div(
    className='rollup-row',
    children=[
        
        html.Div(
            className='rollup-box-tl',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            id='total-exercises-title',
                            className='rollup-title',
                            children=[f'Total Gym Days All Time']
                        ),
                    ]
                ),

                html.Div(
                    className='circle-box-1',
                    children=[
                        html.Div(
                            className='circle-1',
                            children=[
                                html.H1(
                                    id='total-exercises',
                                className='rollup-number',
                                children=['-']
                            ),
                            ]
                        )
                    ],
                ),
            ]
        ),
        html.Div(
            className='rollup-box-tr',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            id='-days-title',
                            className='rollup-title',
                            children=['Placeholder']
                        ),
                    ]
                ),
                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-2',
                            children=[
                                html.H1(
                                id='-days',
                                className='rollup-number',
                                children=['-']
                            ),
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]
),

# html.Div(
#     className='rollup-row',
#     children=[
        
#         html.Div(
#             className='rollup-box-tl',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='pull-days-title',
#                             className='rollup-title',
#                             children=[f'Total Pull Days All Time']
#                         ),
#                     ]
#                 ),

#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-1',
#                             children=[
#                                 html.H1(
#                                     id='pull-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#         html.Div(
#             className='rollup-box-tr',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='leg-days-title',
#                             className='rollup-title',
#                             children=['Total Leg Days All Time']
#                         ),
#                     ]
#                 ),
#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-2',
#                             children=[
#                                 html.H1(
#                                 id='leg-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#     ]
# ),

# html.Div(
#     className='rollup-row',
#     children=[
        
#         html.Div(
#             className='rollup-box-tl',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='arm-days-title',
#                             className='rollup-title',
#                             children=[f'Total Arm Days All Time']
#                         ),
#                     ]
#                 ),

#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-1',
#                             children=[
#                                 html.H1(
#                                     id='arm-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#         html.Div(
#             className='rollup-box-tr',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='ab-days-title',
#                             className='rollup-title',
#                             children=['Total Ab Days All Time']
#                         ),
#                     ]
#                 ),
#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-2',
#                             children=[
#                                 html.H1(
#                                 id='ab-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#     ]
# ),

# html.Div(
#     className='rollup-row',
#     children=[
        
#         html.Div(
#             className='rollup-box-tl',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='other-days-title',
#                             className='rollup-title',
#                             children=[f'Total Other Workouts All Time']
#                         ),
#                     ]
#                 ),

#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-1',
#                             children=[
#                                 html.H1(
#                                     id='other-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#         html.Div(
#             className='rollup-box-tr',
#             children=[
#                 html.Div(
#                     className='title-box',
#                     children=[
#                         html.H3(
#                             id='-days-title',
#                             className='rollup-title',
#                             children=['Placeholder']
#                         ),
#                     ]
#                 ),
#                 html.Div(
#                     className='circle-box',
#                     children=[
#                         html.Div(
#                             className='circle-2',
#                             children=[
#                                 html.H1(
#                                 id='-days',
#                                 className='rollup-number',
#                                 children=['-']
#                             ),
#                             ]
#                         )
#                     ],
#                 ),
#             ]
#         ),
#     ]
# ),

# ============================ Visuals ========================== #

html.Div(
    className='graph-container',
    children=[
        
        # html.H1(
        #     className='visuals-text',
        #     children='Visuals'
        # ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='push-days-title',
                                    className='rollup-title',
                                    children=['Total Push Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='push-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='push-graph',
                            className='wide-graph',
                            figure=push_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='push-bar',
                                    className='graph',
                                    figure=push_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='push-pie',
                                    className='graph',
                                    figure=push_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='pull-days-title',
                                    className='rollup-title',
                                    children=[f'Total Pull Days All Time']
                                ),
                            ]
                        ),

                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                            id='pull-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='pull-graph',
                            className='wide-graph',
                            figure=pull_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='pull-bar',
                                    className='graph',
                                    figure=pull_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='pull-pie',
                                    className='graph',
                                    figure=pull_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='leg-days-title',
                                    className='rollup-title',
                                    children=['Total Leg Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='leg-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='leg-graph',
                            className='wide-graph',
                            figure=leg_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='leg-bar',
                                    className='graph',
                                    figure=leg_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='leg-pie',
                                    className='graph',
                                    figure=leg_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='bicep-days-title',
                                    className='rollup-title',
                                    children=['Total Bicep Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='bicep-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='bicep-graph',
                            className='wide-graph',
                            figure=bicep_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='bicep-bar',
                                    className='graph',
                                    figure=bicep_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='bicep-pie',
                                    className='graph',
                                    figure=bicep_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='tricep-days-title',
                                    className='rollup-title',
                                    children=['Total Tricep Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='tricep-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='tricep-graph',
                            className='wide-graph',
                            figure=tricep_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='tricep-bar',
                                    className='graph',
                                    figure=tricep_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='tricep-pie',
                                    className='graph',
                                    figure=tricep_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='shoulder-days-title',
                                    className='rollup-title',
                                    children=['Total Shoulder Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='shoulder-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='shoulder-graph',
                            className='wide-graph',
                            figure=shoulder_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='shoulder-bar',
                                    className='graph',
                                    figure=shoulder_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='shoulder-pie',
                                    className='graph',
                                    figure=shoulder_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),

        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='calisthenics-days-title',
                                    className='rollup-title',
                                    children=['Total Calisthenics Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='calisthenics-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='calisthenics-graph',
                            className='wide-graph',
                            figure=calisthenics_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='calisthenics-bar',
                                    className='graph',
                                    figure=calisthenics_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='calisthenics-pie',
                                    className='graph',
                                    figure=calisthenics_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),

                
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='ab-days-title',
                                    className='rollup-title',
                                    children=['Total  Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='ab-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='ab-graph',
                            className='wide-graph',
                            figure=ab_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='ab-bar',
                                    className='graph',
                                    figure=ab_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='ab-pie',
                                    className='graph',
                                    figure=ab_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='forearm-days-title',
                                    className='rollup-title',
                                    children=['Total Forearm Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='forearm-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='forearm-graph',
                            className='wide-graph',
                            figure=forearm_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='forearm-bar',
                                    className='graph',
                                    figure=forearm_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='forearm-pie',
                                    className='graph',
                                    figure=forearm_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='cardio-days-title',
                                    className='rollup-title',
                                    children=['Total Cardio Days All Time']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='cardio-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='cardio-graph',
                            className='wide-graph',
                            figure=cardio_line
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='cardio-bar',
                                    className='graph',
                                    figure=cardio_bar
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='cardio-pie',
                                    className='graph',
                                    figure=cardio_pie
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]
),

# ============================ Data Table ========================== #

    html.Div(
        className='data-box',
        children=[
            html.H1(
                id='table-title',
                className='data-title',
                children=f'Fitness Tracker Table {report_year}'
            ),
            
            dash_table.DataTable(
                id='applications-table',
                data=data, # type: ignore
                columns=columns, # type: ignore
                page_size=20,
                sort_action='native',
                filter_action='native',
                row_selectable='multi',
                style_table={
                    'overflowX': 'auto',
                    # 'border': '3px solid #000',
                    # 'borderRadius': '0px'
                },
                style_cell={
                    'textAlign': 'left',
                    'minWidth': '100px', 
                    'whiteSpace': 'normal'
                },
                style_header={
                    'textAlign': 'center', 
                    'fontWeight': 'bold',
                    'backgroundColor': '#34A853', 
                    'color': 'white'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell_conditional=[ # type: ignore
                    # make the index column narrow and centered
                    {'if': {'column_id': '#'},
                    'style': {'width': '20px', 'minWidth': '60px', 'maxWidth': '60px', 'textAlign': 'center'}},

                    {'if': {'column_id': 'Description'},
                    'style': {'width': '350px', 'minWidth': '200px', 'maxWidth': '400px'}},

                    {'if': {'column_id': 'Tags'},
                    'style': {'width': '250px', 'minWidth': '200px', 'maxWidth': '400px'}},

                    {'if': {'column_id': 'Collab'},
                    'style': {'width': '250px', 'minWidth': '200px', 'maxWidth': '400px'}},
                ]
            ),
        ]
    ),
])

# ============================== Callback ========================== #

@app.callback(
    [
        Output('year-subtitle', 'children'),
        Output('total-exercises-title', 'children'),
        Output('total-exercises', 'children'),
        Output('push-days-title', 'children'),
        Output('push-days', 'children'),
        Output('pull-days-title', 'children'),
        Output('pull-days', 'children'),
        Output('leg-days-title', 'children'),
        Output('leg-days', 'children'),
        Output('bicep-days-title', 'children'),
        Output('bicep-days', 'children'),
        Output('tricep-days-title', 'children'),
        Output('tricep-days', 'children'),
        Output('shoulder-days-title', 'children'),
        Output('shoulder-days', 'children'),
        Output('calisthenics-days-title', 'children'),
        Output('calisthenics-days', 'children'),
        Output('ab-days-title', 'children'),
        Output('ab-days', 'children'),
        Output('forearm-days-title', 'children'),
        Output('forearm-days', 'children'),
        Output('cardio-days-title', 'children'),
        Output('cardio-days', 'children'),
        Output('push-graph', 'figure'),
        Output('push-bar', 'figure'),
        Output('push-pie', 'figure'),
        Output('pull-graph', 'figure'),
        Output('pull-bar', 'figure'),
        Output('pull-pie', 'figure'),
        Output('leg-graph', 'figure'),
        Output('leg-bar', 'figure'),
        Output('leg-pie', 'figure'),
        Output('bicep-graph', 'figure'),
        Output('bicep-bar', 'figure'),
        Output('bicep-pie', 'figure'),
        Output('tricep-graph', 'figure'),
        Output('tricep-bar', 'figure'),
        Output('tricep-pie', 'figure'),
        Output('shoulder-graph', 'figure'),
        Output('shoulder-bar', 'figure'),
        Output('shoulder-pie', 'figure'),
        Output('ab-graph', 'figure'),
        Output('ab-bar', 'figure'),
        Output('ab-pie', 'figure'),
        Output('calisthenics-graph', 'figure'),
        Output('calisthenics-bar', 'figure'),
        Output('calisthenics-pie', 'figure'),
        Output('forearm-graph', 'figure'),
        Output('forearm-bar', 'figure'),
        Output('forearm-pie', 'figure'),
        Output('cardio-graph', 'figure'),
        Output('cardio-bar', 'figure'),
        Output('cardio-pie', 'figure'),
        Output('table-title', 'children'),
        Output('applications-table', 'data'),
        Output('applications-table', 'columns'),
    ],
    [Input('year-dropdown', 'value')]
)
def update_dashboard(selected_year):

    # Load data for selected year
    df_year = load_data_for_year(selected_year)
    
    # Get all date columns (everything except Category and Exercise)
    date_columns = [col for col in df_year.columns if col not in ['Category', 'Exercise']]
    
    # Reshape from wide to long format
    df_long = df_year.melt(
        id_vars=['Category', 'Exercise'],
        value_vars=date_columns,
        var_name='Date',
        value_name='Weight'
    )
    
    # Convert Date to datetime with format specification
    df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce', format='mixed')
    df_long = df_long.sort_values('Date')
    
    # Convert Weight to numeric
    df_long['Weight'] = pd.to_numeric(df_long['Weight'], errors='coerce')
    
    # Remove rows with NaN weights
    df_long = df_long.dropna(subset=['Weight'])
    df_long = df_long[df_long['Weight'].notna()]
    df_long = df_long[df_long['Weight'] != '']
    
    # Strip whitespace
    df_long['Category'] = df_long['Category'].astype(str).str.strip()
    df_long['Exercise'] = df_long['Exercise'].astype(str).str.strip()
    
    # Remove duplicates
    df_long = df_long.drop_duplicates(subset=['Category', 'Exercise', 'Date'], keep='first')
    df_long = df_long.reset_index(drop=True)
    
    # Ensure correct types
    df_long['Category'] = df_long['Category'].astype('object')
    df_long['Exercise'] = df_long['Exercise'].astype('object')
    df_long['Date'] = pd.to_datetime(df_long['Date'])
    df_long['Weight'] = df_long['Weight'].astype('float64')
    
    # Calculate total unique gym days (unique dates)
    total = df_long['Date'].nunique()
    
    # Create graphs for each category
    df_push = df_long[df_long['Category'] == 'Push'].reset_index(drop=True)
    push_days = df_push['Date'].nunique() if not df_push.empty else 0
    push_fig = make_line_chart(df_push, f'Push Progress Over Time - {selected_year}')
    df_push_counts = df_push['Exercise'].value_counts().reset_index()
    df_push_counts.columns = ['Exercise', 'Count']

    push_bar_fig = px.bar(
        df_push_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Push Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(size=21, 
            family='Calibri', 
            color='black')
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    push_pie_fig = px.pie(
        df_push_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Push Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_pull = df_long[df_long['Category'] == 'Pull'].reset_index(drop=True)
    pull_days = df_pull['Date'].nunique() if not df_pull.empty else 0
    pull_fig = make_line_chart(df_pull, f'Pull Progress Over Time - {selected_year}')
    df_pull_counts = df_pull['Exercise'].value_counts().reset_index()
    df_pull_counts.columns = ['Exercise', 'Count']
    pull_bar_fig = px.bar(
        df_pull_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Pull Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    pull_pie_fig = px.pie(
        df_pull_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Pull Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_leg = df_long[df_long['Category'] == 'Leg'].reset_index(drop=True)
    leg_days = df_leg['Date'].nunique() if not df_leg.empty else 0
    leg_fig = make_line_chart(df_leg, f'Leg Progress Over Time - {selected_year}')
    df_leg_counts = df_leg['Exercise'].value_counts().reset_index()
    df_leg_counts.columns = ['Exercise', 'Count']
    leg_bar_fig = px.bar(
        df_leg_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Leg Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    leg_pie_fig = px.pie(
        df_leg_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Leg Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    # Calculate bicep days
    df_bicep = df_long[df_long['Category'] == 'Bicep'].reset_index(drop=True)
    bicep_days = df_bicep['Date'].nunique() if not df_bicep.empty else 0
    bicep_fig = make_line_chart(df_bicep, f'Bicep Progress Over Time - {selected_year}')
    df_bicep_counts = df_bicep['Exercise'].value_counts().reset_index()
    df_bicep_counts.columns = ['Exercise', 'Count']
    bicep_bar_fig = px.bar(
        df_bicep_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    bicep_pie_fig = px.pie(
        df_bicep_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_tricep = df_long[df_long['Category'] == 'Tricep'].reset_index(drop=True)
    tricep_days = df_tricep['Date'].nunique() if not df_tricep.empty else 0
    tricep_fig = make_line_chart(df_tricep, f'Tricep Progress Over Time - {selected_year}')
    df_tricep_counts = df_tricep['Exercise'].value_counts().reset_index()
    df_tricep_counts.columns = ['Exercise', 'Count']
    tricep_bar_fig = px.bar(
        df_tricep_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Tricep Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    tricep_pie_fig = px.pie(
        df_tricep_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Tricep Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_shoulder = df_long[df_long['Category'] == 'Shoulder'].reset_index(drop=True)
    shoulder_days = df_shoulder['Date'].nunique() if not df_shoulder.empty else 0
    shoulder_fig = make_line_chart(df_shoulder, f'Shoulder Progress Over Time - {selected_year}')
    df_shoulder_counts = df_shoulder['Exercise'].value_counts().reset_index()
    df_shoulder_counts.columns = ['Exercise', 'Count']
    shoulder_bar_fig = px.bar(
        df_shoulder_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Shoulder Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    shoulder_pie_fig = px.pie(
        df_shoulder_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Shoulder Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_ab = df_long[df_long['Category'] == 'Ab'].reset_index(drop=True)
    ab_days = df_ab['Date'].nunique() if not df_ab.empty else 0
    ab_fig = make_line_chart(df_ab, f'Ab Progress Over Time - {selected_year}')
    df_ab_counts = df_ab['Exercise'].value_counts().reset_index()
    df_ab_counts.columns = ['Exercise', 'Count']
    ab_bar_fig = px.bar(
        df_ab_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Ab Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    ab_pie_fig = px.pie(
        df_ab_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Ab Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_calisthenics = df_long[df_long['Category'] == 'Calisthenics'].reset_index(drop=True)
    calisthenics_days = df_calisthenics['Date'].nunique() if not df_calisthenics.empty else 0
    calisthenics_fig = make_line_chart(df_calisthenics, f'Calisthenics Progress Over Time - {selected_year}')
    df_calisthenics_counts = df_calisthenics['Exercise'].value_counts().reset_index()
    df_calisthenics_counts.columns = ['Exercise', 'Count']
    calisthenics_bar_fig = px.bar(
        df_calisthenics_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Calisthenics Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    calisthenics_pie_fig = px.pie(
        df_calisthenics_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Calisthenics Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_forearm = df_long[df_long['Category'] == 'Forearm'].reset_index(drop=True)
    forearm_days = df_forearm['Date'].nunique() if not df_forearm.empty else 0
    forearm_fig = make_line_chart(df_forearm, f'Forearm Progress Over Time - {selected_year}')
    df_forearm_counts = df_forearm['Exercise'].value_counts().reset_index()
    df_forearm_counts.columns = ['Exercise', 'Count']
    forearm_bar_fig = px.bar(
        df_forearm_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Forearm Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    forearm_pie_fig = px.pie(
        df_forearm_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Forearm Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    df_cardio = df_long[df_long['Category'] == 'Cardio'].reset_index(drop=True)
    cardio_days = df_cardio['Date'].nunique() if not df_cardio.empty else 0
    cardio_fig = make_line_chart(df_cardio, f'Cardio Progress Over Time - {selected_year}')
    df_cardio_counts = df_cardio['Exercise'].value_counts().reset_index()
    df_cardio_counts.columns = ['Exercise', 'Count']
    cardio_bar_fig = px.bar(
        df_cardio_counts, 
        y="Exercise", 
        x='Count', 
        color="Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Cardio Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    cardio_pie_fig = px.pie(
        df_cardio_counts, 
        names="Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Cardio Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    # Prepare table data
    df_indexed = df_long.reset_index(drop=True).copy()
    column_order = ['Date', 'Category', 'Exercise', 'Weight']
    df_indexed = df_indexed[column_order]
    df_indexed.insert(0, '#', df_indexed.index + 1)
    
    table_data = df_indexed.to_dict('records')
    table_columns = [{"name": col, "id": col} for col in df_indexed.columns]
    table_title = f'Fitness Tracker Table - {selected_year}'
    rollup_title = f'Total Gym Days - {selected_year}'
    push_title = f'Total Push Days - {selected_year}'
    pull_title = f'Total Pull Days - {selected_year}'
    leg_title = f'Total Leg Days - {selected_year}'
    bicep_title = f'Total Bicep Days - {selected_year}'
    tricep_title = f'Total Tricep Days - {selected_year}'
    shoulder_title = f'Total Shoulder Days - {selected_year}'
    calisthenics_title = f'Total Calisthenics Days - {selected_year}'
    ab_title = f'Total Ab Days - {selected_year}'
    forearm_title = f'Total Forearm Days - {selected_year}'
    cardio_title = f'Total Cardio Days - {selected_year}'
    year_subtitle = selected_year
    
    return (
        year_subtitle,
        rollup_title,
        total,
        push_title,
        push_days,
        pull_title,
        pull_days,
        leg_title,
        leg_days,
        bicep_title,
        bicep_days,
        tricep_title,
        tricep_days,
        shoulder_title,
        shoulder_days,
        calisthenics_title,
        calisthenics_days,
        ab_title,
        ab_days,
        forearm_title,
        forearm_days,
        cardio_title,
        cardio_days,
        push_fig,
        push_bar_fig,
        push_pie_fig,
        pull_fig,
        pull_bar_fig,
        pull_pie_fig,
        leg_fig,
        leg_bar_fig,
        leg_pie_fig,
        bicep_fig,
        bicep_bar_fig,
        bicep_pie_fig,
        tricep_fig,
        tricep_bar_fig,
        tricep_pie_fig,
        shoulder_fig,
        shoulder_bar_fig,
        shoulder_pie_fig,
        ab_fig,
        ab_bar_fig,
        ab_pie_fig,
        calisthenics_fig,
        calisthenics_bar_fig,
        calisthenics_pie_fig,
        forearm_fig,
        forearm_bar_fig,
        forearm_pie_fig,
        cardio_fig,
        cardio_bar_fig,
        cardio_pie_fig,
        table_title,
        table_data,
        table_columns
    )

print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == '__main__':
    app.run(debug=
                   True)
                #    False)

# -------------------------------------------- KILL PORT ---------------------------------------------------

# netstat -ano | findstr :8050
# taskkill /PID 24772 /F
# npx kill-port 8050

# ---------------------------------------------- Host Application -------------------------------------------

# 1. pip freeze > requirements.txt
# 2. add this to procfile: 'web: gunicorn impact_11_2024:server'
# 3. heroku login
# 4. heroku create
# 5. git push heroku main

# Create venv 
# virtualenv venv 
# source venv/bin/activate # uses the virtualenv

# Update PIP Setup Tools:
# pip install --upgrade pip setuptools

# Install all dependencies in the requirements file:
# pip install -r requirements.txt

# Check dependency tree:
# pipdeptree
# pip show package-name

# Remove
# pypiwin32
# pywin32
# jupytercore

# ----------------------------------------------------

# Name must start with a letter, end with a letter or digit and can only contain lowercase letters, digits, and dashes.

# Heroku Setup:
# heroku login
# heroku create admin-jun-25
# heroku git:remote -a admin-jun-25
# git push heroku main

# Clear Heroku Cache:
# heroku plugins:install heroku-repo
# heroku repo:purge_cache -a mc-impact-11-2024

# Set buildpack for heroku
# heroku buildpacks:set heroku/python

# Get encoded key:
# base64 service_account_file.json