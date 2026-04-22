import difflib
import requests
import streamlit as st
import re
from datetime import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
import io
from PIL import Image, ExifTags
import time

# Fetch settings and image
def fetch_settings_and_image(worksheets):
    sheet = worksheets["settings"]
    data = sheet.get_all_values()  # Get all rows
    settings = {row[0]: row[1] for row in data if len(row) >= 2}  # Create dictionary from key-value pairs
    
    image_url = settings.get('Tittelbilde:')
    if image_url:
        file_id = extract_file_id(image_url)
        image_content = download_image(file_id)
        return settings, image_content
    return settings, None  # No image to display

# Fetch tasks
def fetch_all_tasks(worksheets):
    sheet = worksheets["tasks"]
    data = sheet.get_all_values()[1:]  # Skip header row

    tasks = []
    for row in data:
        if len(row) >= 5:
            question, image_content = handle_image_task(row[1])
            question_data = {
                "text": question,
                "image": image_content
            }
            task = {
                "task_nr": row[0],
                "question": question_data,
                "correct_answer": row[2],
                "hint": row[3],
                "task_password": row[4]
            }
            tasks.append(task)
    return tasks

# Fetch passwords
def fetch_passwords(worksheets):
    sheet = worksheets["users"]
    data = sheet.get_all_values()[1:]  # Skip header row
    psws = {row[1]: row[0] for row in data}  # row[1] is password, row[0] is username
    return psws

# Fetch task orders for all users from the "Lagnavn og passord" worksheet
def get_task_order_for_all_users(worksheets):
    """
    Fetch the task order for all users at once.
    Returns a dictionary where each password is mapped to a list representing the task order.
    """
    sheet = worksheets["users"]
    data = sheet.get_all_values()[1:]  # Skip the header row

    task_orders = {}
    for row in data:
        password = row[1]  # Password is in column B
        task_order_str = row[2] if len(row) > 2 else ""  # Task order is in column C
        task_orders[password] = list(task_order_str) if task_order_str else []

    return task_orders

# Fetch all attempts
def fetch_all_attempts(worksheets):
    sheet = worksheets["answers"]
    records = sheet.get_all_records()
    
    attempts = {}
    for record in records:
        user = record['Lagnavn']
        task_nr = record['Oppgave nr.']
        is_correct = record['Riktig?']

        if user not in attempts:
            attempts[user] = {}

        if is_correct == "Yes":
            attempts[user][task_nr] = "Yes"
        else:
            if attempts[user].get(task_nr) != "Yes":
                attempts[user][task_nr] = attempts[user].get(task_nr, 0) + 1
    return attempts

# Log hint request
def log_hint_request(user, task_nr):
    client = st.session_state.client
    worksheet = client.open("Rebus").worksheet("hint_requests")
    timestamp = get_current_timestamp()
    new_row = [user, task_nr, timestamp]
    worksheet.append_row(new_row)

# Log answer
def log_answer(user, task_nr, submitted_answer, is_correct): 
    client = st.session_state.client
    worksheet = client.open("Rebus").worksheet("answers")
    timestamp = get_current_timestamp()
    correct_str = "Yes" if is_correct else "No"
    new_row = [user, task_nr, submitted_answer, correct_str, timestamp]
    worksheet.append_row(new_row)

# Function to get the current timestamp for Norway (CET/CEST)
def get_current_timestamp():
    norway_tz = pytz.timezone('Europe/Oslo')
    return datetime.now(norway_tz).strftime("%Y-%m-%d %H:%M:%S")

# Function to extract file ID from Google Drive URL
def extract_file_id(url):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("No file ID found in the provided URL")

# Function to download the image content from Google Drive using file ID
def download_image(file_id): 
    url = f"https://drive.google.com/uc?export=view&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.content  # Returns the image content in bytes

# Updated function to check multiple possible answers separated by ";"
def is_similar(user_answer, correct_answer, threshold=0.8): 
    # Split correct_answer by semicolon to handle multiple correct answers
    possible_answers = [ans.strip() for ans in correct_answer.split(";")]
    threshold = float(threshold.replace(',','.')) if ',' in threshold else threshold

    # Check if the user answer is similar to any of the possible answers
    for answer in possible_answers:
        similarity = difflib.SequenceMatcher(None, user_answer.lower(), answer.lower()).ratio()
        if similarity >= threshold:
            return True
    return False

# Function to get the next task's password if it exists
def get_next_task_password(tasks, current_task_nr, task_order): 
    try:
        current_index = task_order.index(current_task_nr)
        # Check if there’s a next task in the user-defined order
        if current_index < len(task_order) - 1:
            next_task_nr = task_order[current_index + 1]
            next_task = next(task for task in tasks if task['task_nr'] == next_task_nr)
            return next_task_nr, next_task['task_password']
        else:
            # Last task reached in the custom order
            return None, None
    except ValueError:
        return None, None

# Function to preload all hints and images for each task
def preload_hints(tasks):
    preloaded_hints = {}
    
    for task in tasks:
        hint_text, image_content_or_url = handle_image_hint(task['hint'])
        preloaded_hints[task['task_nr']] = {
            "text": hint_text,
            "image": image_content_or_url
        }
    
    return preloaded_hints

# Updated function to handle both Google Drive and regular image URLs
def handle_image_hint(hint_text):
    if "bilde:" in hint_text:
        parts = hint_text.split("bilde:")
        text = parts[0].strip()  # Text before "bilde:"
        image_url = parts[1].strip()  # Image URL after "bilde:"
        
        # Check if it's a Google Drive URL
        if "drive.google.com" in image_url:
            try:
                file_id = extract_file_id(image_url)
                image_content = download_image(file_id)
                return text, image_content
            except Exception as e:
                st.write(f"Kunne ikke laste bildet fra Google Drive: {e}")
                return text, None
        else:
            # It's a standard image URL, so return it directly
            return text, image_url
    return hint_text, None

def handle_image_task(task_text):
    if "bilde:" in task_text:
        parts = task_text.split("bilde:")
        text = parts[0].strip()  # Text before "bilde:"
        image_url = parts[1].strip()  # Image URL after "bilde:"
        
        # Check if it's a Google Drive URL
        if "drive.google.com" in image_url:
            try:
                file_id = extract_file_id(image_url)
                image_content = download_image(file_id)
                return text, image_content
            except Exception as e:
                st.write(f"Kunne ikke laste bildet fra Google Drive: {e}")
                return text, None
        else:
            # It's a standard image URL, so return it directly
            return text, image_url
    return task_text, None

# Authenticate and set up the Drive API service
def authenticate_drive():
    scopes = ["https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["google_credentials"], 
        scopes=scopes
    )
    drive_service = build("drive", "v3", credentials=credentials)
    st.session_state.drive_service = drive_service
    return drive_service

# Function to upload an image to a Google Drive folder
def upload_image_to_drive(image, folder_id, file_name):
    drive_service = st.session_state.get('drive_service', authenticate_drive())
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    media = MediaIoBaseUpload(io.BytesIO(image.read()), mimetype="image/jpeg")
    
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    
    return uploaded_file.get("id")

def image_rotation(uploaded_file):
    # Open the image
    image = Image.open(uploaded_file)

    # Rotate the image based on EXIF orientation data if available
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Cases: image has no EXIF orientation data
        pass

    return image


def fetch_extra_task_images(download = False, show_progress = False):
    start_time = time.time()
    
    all_task_imgs = st.session_state.task_imgs
    extra_tasks = st.session_state.extra_tasks
    users = st.session_state.psws.values()

    if show_progress:
        no_imgs = sum(1 for user in users for task in extra_tasks if f'{user}_{task}' in all_task_imgs)
        if no_imgs == 0:
            show_progress = False
        else:
            progress_bar = st.progress(0,'Laster inn bilder...')
            i = 0

    extra_task_images = {}
    for user in users:
        extra_task_images[user] = {}
        for task in extra_tasks:
            file_name = f'{user}_{task}'
            # print(file_name)
            
            if file_name in all_task_imgs:
                file_id = all_task_imgs[file_name]
                img = download_file_by_id(file_id)[0] if download else None
                extra_task_images[user][task] = (img, file_id)
                if show_progress:
                    i += 1
            else:
                extra_task_images[user][task] = False

        if show_progress:
            time.sleep(.1)
            progress_bar.progress(i / no_imgs, 'Laster inn bilder...')
    
    if show_progress:
        time.sleep(.5)
        progress_bar.empty()

    print(f'Extra: {time.time() - start_time}')
    return extra_task_images

def fetch_destination_proof(download = False):
    start_time = time.time()

    destination_proofs = {}
    for psw, user in st.session_state.psws.items():
        task_order = st.session_state.task_orders[psw]
        destinations = [task['correct_answer'].split(";")[0] for task in st.session_state.tasks if task['task_nr'] in task_order]
        destination_proofs[user] = {}
        for destination in destinations:
            file_name = f'{user}_{destination}'

            if file_name in st.session_state.task_imgs:
                file_id = st.session_state.task_imgs[file_name]
                img = download_file_by_id(file_id)[0] if download else None
                destination_proofs[user][destination] = (img, file_id)
            else:
                destination_proofs[user][destination] = False

    print(f'Proof: {time.time() - start_time}')
    return destination_proofs

def fetch_task_imgs(download = False):
    drive_service = st.session_state.get('drive_service', authenticate_drive())
    folder_ids = [st.session_state.dest_proof_folder_id, st.session_state.extra_task_folder_id]

    folder_query = " or ".join([f"'{folder_id}' in parents" for folder_id in folder_ids])
    query = f"mimeType='image/jpeg' and trashed=false and ({folder_query})"

    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name, parents)').execute()
    items = results.get('files', [])
    if items:
        task_imgs = {item['name'].split('.')[0] : item['id'] for item in items}
    else:
        task_imgs = {}
    
    # files_per_folder = {}
    # for folder in folder_ids:
    #     files_per_folder[folder] = []
    #     for item in items:
    #         if folder in item['parents']:
    #             files_per_folder[folder].append(item['name'])

    return task_imgs


def download_file_by_id(file_id):
    drive_service = st.session_state.get('drive_service', authenticate_drive())
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_data.seek(0)
        return (file_data.read(), file_id)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False   

def delete_file_by_id(file_id):
    drive_service = st.session_state.get('drive_service', authenticate_drive())
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
def get_all_img():
    st.session_state.all_img = {}
    drive_service = st.session_state.get('drive_service', authenticate_drive())
    folder_ids = [st.session_state.dest_proof_folder_id, st.session_state.extra_task_folder_id]
    folder_query = " or ".join([f"'{folder_id}' in parents" for folder_id in folder_ids])
    query = f"mimeType='image/jpeg' and trashed=false and ({folder_query})"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name, parents)').execute()
    items = results.get('files', [])
    for item in items:
        file_id = item['id']
        name = item['name']
        st.session_state.all_img[file_id] = (None, name)
            
