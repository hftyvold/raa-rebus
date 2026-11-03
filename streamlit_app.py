import streamlit as st
from initialize import apply_styles, initialize_session_states
from st_login import handle_login, handle_logout
from st_task_tabs import display_task_tab
from st_extra_tasks import extra_tasks
from st_admin import admin_page
from st_location import st_location
import time
apply_styles()
# try:
start_time = time.time()
with st.spinner('Laster inn...'):
    if st.session_state.get('initialized') is not True:
        initialize_session_states()

# Add title
st.title(st.session_state.settings.get('Tittel:', 'Rebus'))

# Add title image
if st.session_state.get('title_image'):
    st.image(st.session_state.title_image)

if st.session_state.get('completed'):
    st.subheader("Gratulerer med fullført rebus!")
    # st.write("Planlegger du allerede ditt neste rebusløp? Ta kontakt med Marcus Nilsen på mail info@raarebus.no")
    handle_logout()
    st.stop()

# Determine sidebar tabs based on authentication status
if not st.session_state.get('authenticated'):
    selected_tab = "Logg inn"
elif st.session_state.authenticated == 'admin':
    admin_page()
else:
    selected_tab = st.sidebar.radio("Velg en fane", ["Logg inn"] + [f"Oppgave {idx + 1}" for idx in range(len(st.session_state.task_order))] + ["Last opp bilder"] + ['Logg ut'])

# Handle Login Tab
if selected_tab == "Logg inn":
    handle_login()
    st_location()  # Show location info on login page
# Handle Task Tabs
elif selected_tab == "Last opp bilder":
    extra_tasks()
elif selected_tab == 'Logg ut':
    handle_logout()
else:
    display_task_tab(selected_tab)
print(f'Total time: {time.time() - start_time}')
# except Exception as e:
#     print(e)
#     st.error("En feil oppstod. Prøv å laste inn siden på nytt.")