import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from config import (GOOGLE_WORKSHEET_ID,
                    DEST_PROOF_FOLDER_ID,
                    EXTRA_TASK_FOLDER_ID)

from utils import (
    fetch_settings_and_image,
    fetch_passwords,
    fetch_all_tasks,
    preload_hints,
    fetch_all_attempts,
    get_task_order_for_all_users,
    fetch_extra_task_images,
    fetch_destination_proof,
    fetch_task_imgs,
)

def apply_styles():
    st.set_page_config(page_title="Raa Rebus",
                       initial_sidebar_state="expanded")
    # Hide Streamlit's footer
    hide_streamlit_style = """
        <style>
        footer {visibility: hidden;}
        [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def initialize_sheets():
    """
    Authenticate and open the Google Sheet once, storing references to each worksheet.
    """
    client = authenticate_gsheet()
    sheet = client.open_by_key(st.session_state.get('google_worksheet_id'))
    worksheets = {
        "settings": sheet.worksheet("Innstillinger"),
        "tasks": sheet.worksheet("Oppgaver, svar og hint"),
        "users": sheet.worksheet("Lagnavn og passord"),
        "answers": sheet.worksheet("answers")
    }
    return worksheets, client

# Authenticate using credentials from Streamlit secrets and include necessary scopes
def authenticate_gsheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["google_credentials"], 
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client


def initialize_session_states():

    st.session_state.initialized = True
    
    st.session_state.google_worksheet_id = GOOGLE_WORKSHEET_ID
    st.session_state.dest_proof_folder_id = DEST_PROOF_FOLDER_ID
    st.session_state.extra_task_folder_id = EXTRA_TASK_FOLDER_ID

    worksheets, client = initialize_sheets()
    st.session_state.client = client
    st.session_state.worksheets = worksheets

    # Fetch settings and cache in session state

    st.session_state.settings, st.session_state.title_image = fetch_settings_and_image(worksheets)

    # Initialize session state variables if they don't exist

    st.session_state.psws = fetch_passwords(worksheets)

    st.session_state.tasks = fetch_all_tasks(worksheets)

    st.session_state.task_orders = get_task_order_for_all_users(worksheets)

    st.session_state.hints = preload_hints(st.session_state.tasks)

    st.session_state.authenticated = False

    st.session_state.hint_requested = {}

    st.session_state.question_answered = {}

    st.session_state.attempts = fetch_all_attempts(worksheets)

    st.session_state.task_unlocked = {}        

    st.session_state.selected_user = list(st.session_state.psws.values())[0]

    st.session_state.task_imgs = fetch_task_imgs()
    # Initialize destination proofs

    st.session_state.proof = fetch_destination_proof()

    st.session_state.extra_tasks = st.session_state.settings['Ekstraoppgaver:'].replace("'", "").split(";")
    st.session_state.extra_task_images = fetch_extra_task_images()
    # Initialize extra tasks
    # if 'extra_tasks' not in st.session_state:
        
    #     st.session_state.extra_tasks = {}
    #     for user in st.session_state.psws.values():
    #         st.session_state.extra_tasks[user] = fetch_extra_task_images(user)
