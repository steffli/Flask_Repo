# -*- coding: utf-8 -*-
import dash

from dash import dcc
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash import html
import dash_html_components as html
from dash.exceptions import PreventUpdate
#import dash_table
from dash import dash_table

import plotly.express as px
from dash.dependencies import Input, Output, State

from zipfile import ZipFile
import urllib.parse
from flask import Flask, send_from_directory

import pandas as pd
import requests
import uuid
import json
import dash_table
from flask_caching import Cache
import re

import utils
import webbrowser

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'GNPS2 - Dataset Browser'

# Optionally turn on caching
if __name__ == "__main__":
    cache = Cache(app.server, config={
        'CACHE_TYPE': "null",
        #'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'temp/flask-cache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 1000000
    })
else:
    WORKER_UP = True
    cache = Cache(app.server, config={
        #'CACHE_TYPE': "null",
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'temp/flask-cache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 120
    })

server = app.server


NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://wang-bioinformatics-lab.github.io/GNPS2_Documentation/img/logo/GNPS2_logo_blue-grey-black.png", width="120px"),
            href="https://gnps2.org",
            className="ms-2"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS2 Sign Up", href="#")),
                dbc.NavItem(dbc.NavLink("Documentation", href="https://wang-bioinformatics-lab.github.io/GNPS2_Documentation/")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

border_style = {
    "border-width": "2px",
    "width": "600px",
    "margin" : "auto",  # Adjust width as needed
}


DASHBOARD = dbc.Container(
    dbc.Card(
        [
            dbc.CardHeader("Welcome to GNPS2! Please sign up here:"),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Label("Username", className="form-label"),
                            dcc.Input(id="username",type="text", className="form-control",style=border_style),
                        ],
                        style={"text-align": "center", "margin-bottom": "10px"},
                    ),
                    html.Div(
                        [
                            html.Label("Email", className="form-label"),
                            dcc.Input(id="email",type="email", className="form-control",style=border_style),
                        ],
                        style={"text-align": "center", "margin-bottom": "10px"},
                    ),
                    html.Div(
                        [
                            html.Label("Password", className="form-label"),
                            dcc.Input(id="password",type="password", className="form-control",style=border_style),
                        ],
                        style={"text-align": "center", "margin-bottom": "10px"},
                    ),
                    html.Div(
                        [
                            html.Label("Invite Token", className="form-label"),
                            dcc.Input(id="invitetoken",type="text", className="form-control",style=border_style),
                        ],
                        style={"text-align": "center", "margin-bottom": "10px"},
                    ),
                    html.Div(
                        [
                            dbc.Button("Create account on all servers",id= "create-all", color="primary", className="mr-2"),
                            html.Span(style={"margin-right": "10px"}), 
                            dbc.Button("Create account on US server",id="create-us", color="primary", className="mr-2"),
                            html.Span(style={"margin-right": "10px"}), 
                            dbc.Button("Create account on DE server",id="create-de", color="primary",className="mr-2"),
                        ],
                        style={"text-align": "center", "margin-top": "20px"},
                    ),
                html.Div(id="output-div"),]
            ),
            
        ]
        ,
        style={"width": "100%", "margin": "auto", "margin-top": "50px"},
    )
)


CONTRIBUTORS_DASHBOARD = [
    dbc.CardHeader(html.H5("Contributors")),
    dbc.CardBody(
        [
            "Mingxun Wang PhD - UC Riverside",
            html.Br(),
            html.Br(),
            html.H5("Citation"),
            html.A('Mingxun Wang, Jeremy J. Carver, Vanessa V. Phelan, Laura M. Sanchez, Neha Garg, Yao Peng, Don Duy Nguyen et al. "Sharing and community curation of mass spectrometry data with Global Natural Products Social Molecular Networking." Nature biotechnology 34, no. 8 (2016): 828. PMID: 27504778', 
                    href="https://www.nature.com/articles/nbt.3597"),
            html.Br(),
            html.Br(),
            html.A('Checkout our other work!', 
                href="https://www.cs.ucr.edu/~mingxunw/")
        ]
    )
]

BODY = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                dbc.Card(DASHBOARD),
                html.Br(),
                dbc.Card(CONTRIBUTORS_DASHBOARD)
            ]),
        ], style={"marginTop": 30}),
    ],
    className="mt-12",
)

app.layout = html.Div(children=[NAVBAR, BODY])
    

# API call to check for valid username: returns json with is_valid_username and valid_reason
def check_user(username):
    if len(username) < 5:
        return True  # Username length is too short
    else:
        url = f"http://ucr-lemon.duckdns.org:4000/user/checkusername?username={username}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["is_valid_username"]:
                return False  # Username is available
            else:
                return True  # Username is not available
        else:
            return False  # Assume username is not available in case of error

def check_password_strength(password):
    length_check = len(password) > 8
    uppercase_check = any(char.isupper() for char in password)
    lowercase_check = any(char.islower() for char in password)
    special_character_check = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    
    return length_check and uppercase_check and lowercase_check and special_character_check

# Additional information about password requirements
password_info = """
Password does not meet the required criteria. Please check the password requirements:
- Be longer than 8 characters 

- Contain at least one uppercase letter

- Contain at least one lowercase letter 

- Contain at least one special character

"""

def login_page():
    return webbrowser.open_new("http://ucr-lemon.duckdns.org:4000/login")


@app.callback(
    Output("output-div", "children"),
    [Input("create-all", "n_clicks"),
     Input("create-us", "n_clicks"),
     Input("create-de", "n_clicks")],
    [State("username", "value"),
     State("email", "value"),
     State("password", "value"),
     State("invitetoken", "value")])


def create_user(click_all, click_us, click_de, username, email, password, invitetoken):
    print(click_all)
    ctx = dash.callback_context

    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "create-all" or button_id == "create-us" or button_id == "create-de":
        if check_user(username):
            return "Username is not available."
        elif not check_password_strength(password):
            return password_info
        else:
            data = {
                "username": username,
                "email": email,
                "password": password,
                "invitetoken": invitetoken
            }
            if button_id == "create-all":
                response = requests.post("http://ucr-lemon.duckdns.org:4000/user/signup", data=data)
            elif button_id == "create-us":
                response = requests.post("http://us-server.com/user/signup", data=data)
            elif button_id == "create-de":
                response = requests.post("http://de-server.com/user/signup", data=data)

            if response.status_code == 200:
                if "invalid token" in response.text.lower():
                    return "User account could not be created. Invalid token."
                elif "username already exists" in response.text.lower():
                    return "User account could not be created. Username already taken."
                else:
                    return "User account created successfully! Please log in."
            else:
                return f"Failed to create user account. Status code: {response.status_code}"

# If the user clicks the "Create Account on US Server" button
    if click_us is not None:
        if not check_password_strength(password):
            return password_info
        elif check_user(username):
            return "Username is not available."
        else:
            data = {
                "username": username,
                "email": email,
                "password": password,
                "invitetoken": invitetoken
            }
            # Make an API request to the US server to create a user account
            response = requests.post("http://us-server.com/user/signup", data=data)
            if response.status_code == 200:
                if "invalid token" in response.text.lower():
                    return "User account could not be created. Invalid token."
                elif "username already exists" in response.text.lower():
                    return "User account could not be created. Username already taken."
                else:
                    return "User account created successfully! Please log in."
            else:
                return f"Failed to create user account. Status code: {response.status_code}"

    # If the user clicks the "Create Account on DE Server" button
    if click_de is not None:
        if not check_password_strength(password):
            return password_info
        elif check_user(username):
            return "Username is not available."
        else:
            data = {
                "username": username,
                "email": email,
                "password": password,
                "invitetoken": invitetoken
            }
            # Make an API request to the DE server to create a user account
            response = requests.post("http://de-server.com/user/signup", data=data)
            if response.status_code == 200:
                if "invalid token" in response.text.lower():
                    return "User account could not be created. Invalid token."
                elif "username already exists" in response.text.lower():
                    return "User account could not be created. Username already taken."
                else:
                    return "User account created successfully! Please log in."
            else:
                return f"Failed to create user account. Status code: {response.status_code}"

                

if __name__ == "__main__":
    app.run_server(debug=True, port=4500, host="0.0.0.0")
