import streamlit as st
from io import BytesIO
from utils import upload_image_to_drive, image_rotation, delete_file_by_id, download_file_by_id
import time



def extra_tasks():
    user = st.session_state.user
    psw = st.session_state.password
    if user not in st.session_state.extra_task_images:
        st.session_state.extra_task_images[user] = {}

    extra_tasks = st.session_state.extra_tasks
    new_extra_tasks = []
    for extra_task in extra_tasks:
        if 'Oppgave ' in extra_task:
            task_letter = extra_task.replace('Oppgave ', '')
            task_external_idx = st.session_state.task_orders[psw].index(task_letter) + 1
            extra_task = f"Oppgave {task_external_idx}"
        new_extra_tasks.append(extra_task)
    if new_extra_tasks != extra_tasks:
        new_extra_tasks = sorted(new_extra_tasks)
        extra_tasks = [x for _, x in sorted(zip(new_extra_tasks, extra_tasks))]

    task_text = st.session_state.settings['Ekstraoppgaver forklaring:'].replace("'", "").split(";")
    if len(task_text) != len(extra_tasks):
        task_text = [""] * len(extra_tasks)
    for task, text, new_task in zip(extra_tasks, task_text, new_extra_tasks):
        if f"{task}_visible" not in st.session_state:
            st.session_state[f"{task}_visible"] = False

        st.subheader(new_task)
        if text:
            st.write(text)
        if not st.session_state.extra_task_images[user].get(task, False):
            img = st.file_uploader('Ta eller last opp bilde:', key=task, label_visibility='collapsed')
            if img:
                rotated_img = image_rotation(img)
                
                # Convert the rotated image to a BytesIO object for upload
                file_name = f"{st.session_state.user}_{task}.jpg" #_{get_current_timestamp().replace(' ', '_')}
                img_buffer = BytesIO()
                rotated_img.save(img_buffer, format="JPEG")
                img_buffer.seek(0)  # Go to the start of the BytesIO object

                # Folder ID where you want to save the image in Google Drive
                folder_id = st.session_state.get('extra_task_folder_id')

                if img_buffer:
                    # Upload the image to Google Drive
                    file_id = upload_image_to_drive(img_buffer, folder_id, file_name)
                    st.session_state.extra_task_images[user][task] = (rotated_img, file_id)
                    time.sleep(.5)
                    st.rerun()
                else:
                    st.image(rotated_img)
        else:
            st.success("Opplasting vellykket!")
            # Button to toggle the visibility of the image
            if st.button('Se bildet' if not st.session_state[f"{task}_visible"] else 'Skjul bildet', key=task+'_se'):
                # Toggle the visibility state
                st.session_state[f"{task}_visible"] = not st.session_state[f"{task}_visible"]
                st.rerun()

            # Conditionally display the image based on visibility state
            if st.session_state[f"{task}_visible"]:
                # Load if image is not loaded
                img, file_id = st.session_state.extra_task_images[user][task]
                if file_id and not img:
                    st.session_state.extra_task_images[user][task] = download_file_by_id(file_id)
                    st.rerun()
                else:
                    st.image(st.session_state.extra_task_images[user][task][0])

            if st.button('Slett og last opp nytt bilde', key=task+'_nytt'):
                if delete_file_by_id(st.session_state.extra_task_images[user][task][1]):
                    st.session_state.extra_task_images[user][task] = False
                    st.rerun()
                else:
                    st.error("Noe gikk galt, prøv igjen. Last inn appen på nytt om problemet vedvarer.")