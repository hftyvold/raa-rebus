import streamlit as st
from utils import (get_all_img,
                   delete_file_by_id,
                   fetch_extra_task_images,
                   fetch_destination_proof,
                   fetch_task_imgs,
                   download_file_by_id,
                   )
from st_login import handle_logout

def admin_page():
 
    selected_tab = st.sidebar.radio("Velg en fane", ['Logg inn',
                                                     'Se poeng',
                                                     'Bilder: Destinasjonsbevis',
                                                     'Bilder: Ekstraoppgaver',
                                                     'Slett bilder',
                                                     'Logg ut'])

    if selected_tab == 'Logg inn':
        st.write("Du er logget inn som admin. Velg aktiviteter ved å trykke på pilen oppe i venstre hjørne.")
    elif selected_tab == 'Se poeng':
        st.header('Poeng')
        st.write('Kommer')
    elif selected_tab == 'Bilder: Destinasjonsbevis':
        st.header(selected_tab)
        view_destination_proofs()
    elif selected_tab == 'Bilder: Ekstraoppgaver':
        st.header(selected_tab)
        view_extra_task_imgs()
    elif selected_tab == 'Slett bilder':
        view_and_del_imgs()
    elif selected_tab == 'Logg ut':
        handle_logout()

    st.stop()

def view_destination_proofs():
    users = st.session_state.psws.values()
    selected_user = st.session_state.selected_user

    if st.button('Update'):
        st.write('Henter bilder...')
        st.session_state.task_imgs = fetch_task_imgs()
        st.session_state.proof = fetch_destination_proof(download=True)
        # st.session_state.extra_tasks = fetch_extra_task_images(download=True)
        st.rerun()

    no_of_imgs = sum(1 for user in users for task, img in st.session_state.proof[user].items() if img)
    st.write(f'Totalt antall bilder lastet opp: {no_of_imgs}')
    
    st.divider()
    user = st.selectbox('Velg lag:', users, index=list(users).index(selected_user))
    if st.session_state.selected_user != user:
        st.session_state.selected_user = user
        st.rerun()

    destinations = st.session_state.proof[user].keys()
    if user:
        for destination in destinations:
            st.subheader(f'{destination}:')
            img, file_id = st.session_state.proof[user][destination] if st.session_state.proof[user][destination] else (False, False)
            if img:
                st.image(img)
            elif file_id and not img:
                st.warning('Bildet er ikke lastet inn. Last inn med knappen under eller trykk "Update" øverst for å laste inn alle bilder.')
                if st.button('Last inn bilde', key=f'{file_id}_load'):
                    st.session_state.proof[user][destination] = download_file_by_id(file_id)
                    st.rerun()
            else:
                st.write('Ingen bilde')


def view_extra_task_imgs():
    users = st.session_state.psws.values()
    selected_user = st.session_state.selected_user

    if st.button('Update'):
        st.session_state.task_imgs = fetch_task_imgs()
        # st.session_state.proof = fetch_destination_proof(download=True)
        st.session_state.extra_task_images = fetch_extra_task_images(download=True, show_progress=True)
        st.rerun()

    no_of_imgs = sum(1 for user in users for task, img in st.session_state.extra_task_images[user].items() if img)
    st.write(f'Totalt antall bilder lastet opp: {no_of_imgs}')
    
    st.divider()
    user = st.selectbox('Velg lag:', users, index=list(users).index(selected_user))
    if st.session_state.selected_user != user:
        st.session_state.selected_user = user
        st.rerun()

    extra_tasks = st.session_state.extra_tasks

    if user:
        for task in extra_tasks:
            st.subheader(f'{task}:')

            img, file_id = st.session_state.extra_task_images[user][task] if st.session_state.extra_task_images[user][task] else (False, False)
            if img:
                st.image(img)
            elif file_id and not img:
                st.warning('Bildet er ikke lastet inn. Last inn med knappen under eller trykk "Update" øverst for å laste inn alle bilder.')
                if st.button('Last inn bilde', key=f'{file_id}_load'):
                    st.session_state.extra_task_images[user][task] = download_file_by_id(file_id)
                    st.rerun()
            else:
                st.write('Ingen bilde')


def view_and_del_imgs():
    st.header('Alle bilder')
    if 'all_img' not in st.session_state:
        get_all_img()
        st.rerun()

    if st.button('Update'):
        st.write('Henter bilder...')
        get_all_img()
        st.rerun()

    all_img = st.session_state.all_img
    no_of_imgs = len(all_img)

    if no_of_imgs == 0:
        st.write('Ingen bilder')
        st.stop()
    else:
        st.write(f'Totalt antall bilder lastet opp: {no_of_imgs}')
    
    # Slett bilder
    st.divider()
    st.subheader('Slett bilder')
    if 'confirm_delete_all' not in st.session_state:
        st.session_state.confirm_delete_all = False

    if st.session_state.confirm_delete_all:
        st.write(f'Er du sikker på at du vil slette alle bilder?')
        if st.button('Ja, slett alle'):
            no_of_deleted_img = no_of_imgs
            for file_id in all_img.keys():
                delete_file_by_id(file_id)
            st.session_state.confirm_delete_all = False
            st.session_state.all_img = {}
            st.success(f'{no_of_deleted_img} bildefiler slettet!')
            st.session_state["all_img_visible"] = False
            st.stop()
        if st.button('Nei, avbryt'):
            st.session_state.confirm_delete_all = False
    else:
        if st.button('Slett alle bilder'):
            st.session_state.confirm_delete_all = True
            st.rerun()

    # Se alle
    st.divider()
    st.subheader('Se bilder')
    if "all_img_visible" not in st.session_state:
        st.session_state["all_img_visible"] = False
    if st.button('Se alle bilder' if not st.session_state["all_img_visible"] else 'Skjul alle bilder'):
        # Toggle the visibility state
        st.session_state["all_img_visible"] = not st.session_state["all_img_visible"]
        st.rerun()

    # Conditionally display the image based on visibility state
    if st.session_state["all_img_visible"]:

        for file_id, (img, name) in list(all_img.items()):
            st.divider()
            st.write(name)
            if img:
                st.image(img, width=150)
            else:
                st.warning('Bildet er ikke lastet inn.')
                if st.button('Last inn bilde', key=f'{file_id}_load'):
                    st.session_state.all_img[file_id] = (download_file_by_id(file_id)[0], name)
                    st.rerun()
            if st.button('Delete', key=f'{file_id}_del'):
                delete_file_by_id(file_id)
                del st.session_state.all_img[file_id]
                st.rerun()