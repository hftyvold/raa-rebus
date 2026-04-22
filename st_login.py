import streamlit as st


def handle_login():
    st.subheader("Logg inn")

    if not st.session_state.authenticated:
        psw = st.text_input("Skriv inn lagpassord:", type="password")
        submit = st.button("Send inn")

        if submit and psw != '':
            if psw == st.session_state.settings['Passord admin:']:
                st.session_state.authenticated = 'admin'
                st.rerun()
            if psw in st.session_state.psws:
                st.session_state.authenticated = True
                st.session_state.password = psw  # Save the password in session
                st.session_state.user = st.session_state.psws[psw]  # Save the username
                st.session_state.task_order = st.session_state.task_orders[psw]
                st.session_state.user_attempts = st.session_state.attempts.get(st.session_state.user, {})
                
                # Initialize task unlocking based on task order and previous attempts
                task_order = st.session_state.task_order
                st.session_state.task_unlocked = {task_order[0]: True}  # Unlock first task in order
                for idx, task_nr in enumerate(task_order[1:], 1):  # Start checking from the second task
                    prev_task_nr = task_order[idx - 1]
                    prev_attempts = st.session_state.attempts.get(st.session_state.user, {}).get(prev_task_nr, 0)
                    if prev_attempts == "Yes" or prev_attempts >= int(st.session_state.settings.get("Antall forsøk:", 2)):
                        st.session_state.task_unlocked[task_nr] = True
                    else:
                        st.session_state.task_unlocked[task_nr] = False

                st.rerun()

            else:
                st.write('Ugyldig passord!')
    else:
        st.write(f"Dere er logget inn som {(st.session_state.user)}. Velg oppgaver ved å trykke på pilen oppe i venstre hjørne. Her avgir dere svar og får hint. Lykke til!")

def handle_logout():
    # st.subheader("Logg ut")
    if st.button('Logg ut'):
        st.session_state.authenticated = False
        st.session_state.completed = False
        st.rerun()