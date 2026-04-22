import streamlit as st
import time

from utils import (is_similar,
                   log_answer,
                   get_next_task_password,
                   log_hint_request,
                   upload_image_to_drive,
                   delete_file_by_id,
                   download_file_by_id,
                   )

def display_task_tab(selected_tab):
    # Check login
    if not st.session_state.authenticated:
        st.write("Vennligst logg inn for å se oppgavene.")
        st.stop()
    else:
        user = st.session_state.user
    
    # Get current and previous task, if valid
    ## Current
    selected_task_idx = int(selected_tab.split(" ")[1]) - 1  # Get task index (1-based)
    selected_task_letter = st.session_state.task_order[selected_task_idx]
    try:
        selected_task = next(task for task in st.session_state.tasks if task["task_nr"] == selected_task_letter)
    except StopIteration:
        st.error(f'ValueError: Oppgave "{selected_task_letter}" er ikke definert!')
        st.stop()
    next_destination = selected_task['correct_answer'].split(";")[0]
    task_password = selected_task["task_password"]
    user_attempts = st.session_state.attempts.get(user, {}).get(selected_task['task_nr'], 0)
    max_attempts = int(st.session_state.settings.get("Antall forsøk:", 2))

    ## Previous
    previous_task_idx = selected_task_idx - 1
    previous_task_letter = st.session_state.task_order[previous_task_idx]

    try:
        previous_task = next(task for task in st.session_state.tasks if task["task_nr"] == previous_task_letter)
    except StopIteration:
        st.error(f'ValueError: Oppgave "{previous_task_letter}" er ikke definert!')
        st.stop()
    current_destination = previous_task['correct_answer'].split(";")[0]

    # Check if task is unlocked
    if not st.session_state.task_unlocked.get(selected_task['task_nr'], False):
        # Display message if the task is locked
        if previous_task_idx >= 0:
            previous_task_nr = st.session_state.task_order[previous_task_idx]
            st.write(f"Vennligst fullfør oppgave {previous_task_idx + 1} for å låse opp denne oppgaven.")
        else:
            st.write("Denne oppgaven er låst.")
        st.stop()
    # else:

    # Check if proof for the task is needed, and if so, uploaded
    if selected_task_idx + 1 <= 2 or True:
        pass
    elif not st.session_state.proof[user][current_destination]:
        st.write(f"Ta et bilde av fasaden til {current_destination} for å låse opp oppgaven:")
        if st.checkbox('Aktiver kamera'):
            img = st.camera_input(f"Ta et bilde av fasaden til {current_destination}:", label_visibility='collapsed')
            if img:
                if st.button('Last opp bilde'):
                    file_id = upload_image_to_drive(img, "1i3CB4odMcnmGZf0lNHawviCIoCrZngw1", f'{user}_{current_destination}')
                    st.session_state.proof[user][current_destination] = (img, file_id)

                    time.sleep(.5)
                    st.rerun()
                else:
                    st.stop()
            else:
                st.stop()
        else:
            st.stop()
    elif st.session_state.proof[user][current_destination]:
        st.success("Opplasting vellykket!")
        if f"{selected_task['task_nr']}_visible" not in st.session_state:
            st.session_state[f"{selected_task['task_nr']}_visible"] = False
        # Button to toggle the visibility of the image
        if st.button('Se bildet' if not st.session_state[f"{selected_task['task_nr']}_visible"] else 'Skjul bildet', key="proof_visible"):
            # Toggle the visibility state
            st.session_state[f"{selected_task['task_nr']}_visible"] = not st.session_state[f"{selected_task['task_nr']}_visible"]
            st.rerun()

        # Conditionally display the image based on visibility state
        if st.session_state[f"{selected_task['task_nr']}_visible"]:
            # Load if image is not loaded
            img, file_id = st.session_state.proof[user][current_destination]
            if file_id and not img:
                st.session_state.proof[user][current_destination] = download_file_by_id(file_id)
                st.rerun()
            else:
                st.image(st.session_state.proof[user][current_destination][0])

        if st.button('Slett og last opp nytt bilde', key=current_destination+'_nytt'):
            if delete_file_by_id(st.session_state.proof[user][current_destination][1]):
                st.session_state.proof[user][current_destination] = False
                st.rerun()
            else:
                st.error("Noe gikk galt, prøv igjen. Last inn appen på nytt om problemet vedvarer.")
        

    # Check if the answer is already correct
    if user_attempts == "Yes" or (selected_task['task_nr'] in st.session_state.question_answered and st.session_state.question_answered[selected_task['task_nr']]):
        st.write("Riktig svar!")

        # Unlock the next task in the sequence
        next_task_nr = st.session_state.task_order[selected_task_idx + 1] if selected_task_idx + 1 < len(st.session_state.task_order) else None
        if next_task_nr:
            st.session_state.task_unlocked[next_task_nr] = True

        # Show the next task's password, if available
        next_task_nr, next_task_password = get_next_task_password(st.session_state.tasks, selected_task['task_nr'], st.session_state.task_order)
        if next_task_nr:
            next_task_external_idx = st.session_state.task_order.index(next_task_nr) + 1
            # st.write(f"Ta turen til {next_destination}!")
            st.write('Gå videre til neste oppgave!')
            if next_task_password and next_task_password != "-":
                st.write(f"For å låse opp oppgave {next_task_external_idx}, skriv inn passord: {next_task_password}")
        else:
            st.write(f"Gratulerer, dere er ferdige med rebusløpet! Nå gjelder det bare å komme seg raskest mulig til {next_destination}!")
            if st.button("Avslutt rebus"):
                st.session_state.completed = True
                st.rerun()

    # Check if maximum attempts are reached
    elif user_attempts >= max_attempts:
        st.write("Dessverre feil svar igjen... Dere får 0 poeng på oppgaven")

        # Unlock the next task in the sequence if max attempts reached
        next_task_nr = st.session_state.task_order[selected_task_idx + 1] if selected_task_idx + 1 < len(st.session_state.task_order) else None
        if next_task_nr:
            st.session_state.task_unlocked[next_task_nr] = True

        # Get next task information if applicable
        next_task_nr, next_task_password = get_next_task_password(st.session_state.tasks, selected_task['task_nr'], st.session_state.task_order)
        if next_task_nr:
            next_task_external_idx = st.session_state.task_order.index(next_task_nr) + 1
            # st.write(f"Ta turen til {next_destination}!")
            st.write('Gå videre til neste oppgave!')
        else:
            st.write(f"Gratulerer, dere er ferdige med rebusløpet! Nå gjelder det bare å komme seg raskest mulig til {next_destination}!")
            if st.button("Avslutt rebus"):
                st.session_state.completed = True
                st.rerun()

    
    else:
        # Automatically unlock tasks if the password is "-"
        if task_password == "-":
            st.session_state.task_unlocked[selected_task['task_nr']] = True

        # Task requires a password to unlock
        if selected_task['task_nr'] not in st.session_state.task_unlocked:
            task_psw = st.text_input(f"Skriv inn passord for oppgave {selected_task_idx + 1}:", type="password")
            unlock_submit = st.button(f"Lås opp oppgave {selected_task_idx + 1}")

            # Check if the task password is correct
            if unlock_submit and task_psw == task_password:
                st.session_state.task_unlocked[selected_task['task_nr']] = True  # Unlock the task
                st.write(f"Oppgave {selected_task_idx + 1} er låst opp!")
            elif unlock_submit:
                st.write("Feil passord. Prøv igjen.")

        # If the task is unlocked, display the task content
        if selected_task['task_nr'] in st.session_state.task_unlocked:
            # Display the selected task's question with external numbering
            st.subheader(f"Oppgave {selected_task_idx + 1}")
            question_data = selected_task['question']
            if question_data["text"] != "-":
                if question_data['text']:
                    st.write(f"Spørsmål: {question_data['text']}")

                # Display the preloaded hint image if available
                if question_data["image"]:
                    if isinstance(question_data["image"], bytes):  # Google Drive image content
                        st.image(question_data["image"])
                    else:  # Regular image URL
                        st.image(question_data["image"])

            # Ask for answer input
            wrong_point = int(st.session_state.settings.get('Poeng feil', '1').replace('−', '-'))
            answer_input = st.text_input(f"Skriv inn svaret på oppgave {selected_task_idx + 1}. For feil svar trekkes {-wrong_point} poeng fra maksimal poengsum!")

            # Submit answer button
            answer_submit = st.button(f"Send inn svaret")

            # Check if the submitted answer is "close enough" to the correct answer
            if answer_submit and answer_input != '':
                is_correct = is_similar(answer_input, selected_task['correct_answer'], st.session_state.settings.get('Likhetskrav:', 0.8))
                log_answer(user, selected_task['task_nr'], answer_input, is_correct)  # Log answer

                if is_correct:
                    st.write("Riktig svar!")
                    st.session_state.question_answered[selected_task['task_nr']] = True
                    st.rerun()

                else:
                    # Ensure user and task exist in the session state attempts dictionary
                    if user not in st.session_state.attempts:
                        st.session_state.attempts[user] = {}
                    if selected_task['task_nr'] not in st.session_state.attempts[user]:
                        st.session_state.attempts[user][selected_task['task_nr']] = 0

                    # Increment the attempt count
                    st.session_state.attempts[user][selected_task['task_nr']] += 1
                    user_attempts = st.session_state.attempts[user][selected_task['task_nr']]
                    max_attempts = int(st.session_state.settings['Antall forsøk:'])

                    # Display error message if max attempts are reached
                    if int(user_attempts) >= int(max_attempts):
                        st.rerun()
                    else:
                        # Display the incorrect attempt message with attempt count
                        st.write("Svaret er dessverre feil... Prøv en siste gang, men svarer dere feil nå blir det 0 poeng på oppgaven!")
                        st.write(f"Antall forsøk: {user_attempts}/{max_attempts}")

            # Show the attempt count if the task is not yet answered correctly
            elif not st.session_state.question_answered.get(selected_task['task_nr'], False):
                user_attempts = st.session_state.attempts.get(user, {}).get(selected_task['task_nr'], 0)
                max_attempts = int(st.session_state.settings['Antall forsøk:'])
                st.write(f"Antall forsøk: {user_attempts}/{max_attempts}")

            # Only show the hint button if the answer is not correct yet, hint not requested, and max attempts not reached
            if not st.session_state.question_answered.get(selected_task['task_nr'], False) and user_attempts < max_attempts:
                # Check if hint has already been requested
                if not st.session_state.hint_requested.get(selected_task['task_nr'], False):
                    st.subheader("Hint")
                    hint_points = int(st.session_state.settings.get('Poeng hint', '2').replace('−', '-'))
                    st.write(f"Trykk på knappen for å motta hint. Merk at det trekkes {-hint_points} poeng fra maksimal poengsum idet dere trykker på knappen!")
                    if st.button(f"Hint på oppgave {selected_task_idx + 1}"):
                        st.session_state.hint_requested[selected_task['task_nr']] = True
                        log_hint_request(user, selected_task['task_nr'])  # Log the hint request

                # Display the hint if it was requested
                if st.session_state.hint_requested.get(selected_task['task_nr'], False):
                    hint_data = st.session_state.hints[selected_task['task_nr']]
                    if hint_data["text"]:
                        st.write(hint_data["text"])
                    
                    # Display the preloaded hint image if available
                    if hint_data["image"]:
                        if isinstance(hint_data["image"], bytes):  # Google Drive image content
                            st.image(hint_data["image"])
                        else:  # Regular image URL
                            st.image(hint_data["image"])
