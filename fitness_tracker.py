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
                print(f"Worksheet Jason_{yr} not found, skipping...")
                continue
        
        if dfs:
            # Combine all dataframes
            combined_df = pd.concat(dfs, ignore_index=True)
            return combined_df.copy()
        else:
            # Return empty dataframe if no data found
            return pd.DataFrame()
    else:
        worksheet = sheet.worksheet(f"Jason_{year}")
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

# Convert Date to datetime
df_long['Date'] = pd.to_datetime(df_long['Date'])

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

# ========================= Pull Exercises =========================== #

# Filter for Pull category and reset index
df_pull = df_long[df_long['Category'] == 'Pull'].reset_index(drop=True)

pull_line = make_line_chart(df_pull, 'Pull Progress Over Time')

# ========================= Leg Exercises =========================== #

# Filter for Leg category and reset index
df_leg = df_long[df_long['Category'] == 'Leg'].reset_index(drop=True)

leg_line = make_line_chart(df_leg, 'Leg Progress Over Time')

# ========================= Bicep Exercises =========================== #

# Filter for Bicep category and reset index
df_bicep = df_long[df_long['Category'] == 'Bicep'].reset_index(drop=True)

bicep_line = make_line_chart(df_bicep, 'Bicep Progress Over Time')

# ========================= Tricep Exercises =========================== #

# Filter for Tricep category and reset index
df_tricep = df_long[df_long['Category'] == 'Tricep'].reset_index(drop=True)

tricep_line = make_line_chart(df_tricep, 'Tricep Progress Over Time')

# ========================= Shoulder Exercises =========================== #

# Filter for Shoulder category and reset index
df_shoulder = df_long[df_long['Category'] == 'Shoulder'].reset_index(drop=True)

shoulder_line = make_line_chart(df_shoulder, 'Shoulder Progress Over Time')

# ========================= Forearm Exercises =========================== #

# Filter for Forearm category and reset index
df_forearm = df_long[df_long['Category'] == 'Forearm'].reset_index(drop=True)

forearm_line = make_line_chart(df_forearm, 'Forearm Progress Over Time')

# ========================= Ab Exercises =========================== #

# Filter for Ab category and reset index
df_ab = df_long[df_long['Category'] == 'Ab'].reset_index(drop=True)

ab_line = make_line_chart(df_ab, 'Ab Progress Over Time')

# ========================= Calisthenics Exercises =========================== #

# Filter for Calisthenics category and reset index
df_calisthenics = df_long[df_long['Category'] == 'Calisthenics'].reset_index(drop=True)

calisthenics_line = make_line_chart(df_calisthenics, 'Calisthenics Progress Over Time')

# =========================  Other Exercises =========================== #

df_other = df_long[df_long['Category'] == 'Other'].reset_index(drop=True)
other_line = make_line_chart(df_other, 'Other Progress Over Time')

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
                    f"Jason's Fitness Tracker",  
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
                                {'label': '2024', 'value': '2024'},
                                {'label': '2025', 'value': '2025'},
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
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-1',
                            children=[
                                html.H1(
                                    id='total-exercises',
                                className='rollup-number',
                                children=[total_gym_days]
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
                            className='circle-2',
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
    ]
),

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
                            className='circle-1',
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
            className='rollup-box-tr',
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
                            className='circle-2',
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
    ]
),

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
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='push-graph',
                            className='wide-graph',
                            figure=push_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),

        
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),

                
        html.Div(
            className='graph-row',
            children=[
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
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='other-graph',
                            className='wide-graph',
                            figure=other_line
                        )
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
        Output('push-graph', 'figure'),
        Output('pull-graph', 'figure'),
        Output('leg-graph', 'figure'),
        Output('bicep-graph', 'figure'),
        Output('tricep-graph', 'figure'),
        Output('shoulder-graph', 'figure'),
        Output('ab-graph', 'figure'),
        Output('calisthenics-graph', 'figure'),
        Output('other-graph', 'figure'),
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
    
    # Convert Date to datetime
    df_long['Date'] = pd.to_datetime(df_long['Date'])
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
    
    df_pull = df_long[df_long['Category'] == 'Pull'].reset_index(drop=True)
    pull_days = df_pull['Date'].nunique() if not df_pull.empty else 0
    pull_fig = make_line_chart(df_pull, f'Pull Progress Over Time - {selected_year}')
    
    df_leg = df_long[df_long['Category'] == 'Leg'].reset_index(drop=True)
    leg_days = df_leg['Date'].nunique() if not df_leg.empty else 0
    leg_fig = make_line_chart(df_leg, f'Leg Progress Over Time - {selected_year}')
    
    df_bicep = df_long[df_long['Category'] == 'Bicep'].reset_index(drop=True)
    bicep_fig = make_line_chart(df_bicep, f'Bicep Progress Over Time - {selected_year}')
    
    df_tricep = df_long[df_long['Category'] == 'Tricep'].reset_index(drop=True)
    tricep_fig = make_line_chart(df_tricep, f'Tricep Progress Over Time - {selected_year}')
    
    df_shoulder = df_long[df_long['Category'] == 'Shoulder'].reset_index(drop=True)
    shoulder_fig = make_line_chart(df_shoulder, f'Shoulder Progress Over Time - {selected_year}')
    
    df_ab = df_long[df_long['Category'] == 'Ab'].reset_index(drop=True)
    ab_fig = make_line_chart(df_ab, f'Ab Progress Over Time - {selected_year}')
    
    df_calisthenics = df_long[df_long['Category'] == 'Calisthenics'].reset_index(drop=True)
    calisthenics_fig = make_line_chart(df_calisthenics, f'Calisthenics Progress Over Time - {selected_year}')
    
    df_other = df_long[df_long['Category'] == 'Other'].reset_index(drop=True)
    other_fig = make_line_chart(df_other, f'Other Progress Over Time - {selected_year}')
    
    # Prepare table data
    df_indexed = df_long.reset_index(drop=True).copy()
    column_order = ['Date', 'Category', 'Exercise', 'Weight']
    df_indexed = df_indexed[column_order]
    df_indexed.insert(0, '#', df_indexed.index + 1)
    
    table_data = df_indexed.to_dict('records')
    table_columns = [{"name": col, "id": col} for col in df_indexed.columns]
    table_title = f'Fitness Tracker Table {selected_year}'
    rollup_title = f'Total Gym Days {selected_year}'
    push_title = f'Total Push Days {selected_year}'
    pull_title = f'Total Pull Days {selected_year}'
    leg_title = f'Total Leg Days {selected_year}'
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
        push_fig,
        pull_fig,
        leg_fig,
        bicep_fig,
        tricep_fig,
        shoulder_fig,
        ab_fig,
        calisthenics_fig,
        other_fig,
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