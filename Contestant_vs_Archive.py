import streamlit as st
from footer import footer
from utils import *


def init(totq: int = 6, 
         contestant: str = "Default",
         source: str = "JArchive",
         post_init = False):
    if not post_init:
        # Used to prevent "please make a guess" warning when starting a brand new session
        st.session_state.start = 0  
        # Distinguish between a brand new session and restart
        st.session_state.input = 0
        # Track number of points scored in a game
        st.session_state.points = 0
        # Track total number of questions received in a game
        st.session_state.nq = 0
        # Track number of questions answered correctly in a game
        st.session_state.answered = 0
        st.session_state.contestant = contestant
        st.session_state.source = source

    st.session_state.contestant = contestant
    st.session_state.source = source
    st.session_state.start = 0
    if st.session_state.source == "JArchive":
        st.session_state.question = generate_question_from_archive(None, None)
    else:
        st.session_state.question = generate_question_from_chatgpt(None, None)
    st.session_state.totq = totq


def restart():
    init(st.session_state.totq,
         st.session_state.contestant,
         st.session_state.source,
         post_init=True)
    st.session_state.input += 1


def main():

    st.title("This is Jeopardy!")
    if 'contestant' not in st.session_state:
        init()
    st.write(f"##### **Contestant Name: {st.session_state.contestant}**") 
    st.write(f"##### **Question Source: {st.session_state.source}**")
    st.write("")

    if 'question' not in st.session_state:
        init()

    reset, points, questions, settings = st.columns([2, 2, 2, 6], gap="small")
    reset.button(f'Reset', on_click=init)

    with settings.expander('Settings'):
        st.text_input('Contestant Name', key='contestant', on_change=restart)
        st.radio('Question Source:', ('JArchive', 'ChatGPT'), key='source', on_change=restart, horizontal=True)
        #st.select_slider('Number of Questions', list(range(1, 6)), 3, key='totq', on_change=restart)
    
    header1, header2, header3, placeholder, debug, end = st.empty(), st.empty(), st.empty(), st.empty(), st.empty(), st.empty()

    category = st.session_state.question[0]
    question = st.session_state.question[1]
    answer = st.session_state.question[2]
    value = st.session_state.question[3]
    prev_guess = ''

    header1.write(f"**Category:** {category}")
    header2.write(f"**Clue:** {question}")
    header3.write(f"**Points:** {value}")
    guess = placeholder.text_input(f'Response',key=st.session_state.input).lower()
     
    if not guess:
        if st.session_state.start != 0 and guess == prev_guess:
            debug.warning('Please make a guess')
    else:
        prev_guess = guess
        sresponse = sanitize(guess)
        sanswer = sanitize(answer)
        sanswer = sanswer.split()[-1]
        
        if (compare_strings(sresponse, sanswer) >= 0.5):
            debug.success(f"**Correct**, the answer was: {answer}! 🎈")
            st.session_state.points += value
            st.session_state.answered += 1
        else:
            debug.error(f"**Incorrect**, the answer was: {answer}! 😓")
            st.session_state.points -= value
        
        st.session_state.nq += 1
            
        if st.session_state.nq < st.session_state.totq:            
            st.button('Next', on_click=restart)

    if st.session_state.nq == st.session_state.totq:
        score = f"{st.session_state.points} ({st.session_state.answered}/{st.session_state.nq})"
        end.error(f"**Sorry, Game Over** Your score: {score} 😓")
        st.button('Play again?', on_click=init)
        
    questions.button(f'Q: {st.session_state.nq}' if st.session_state.nq <= st.session_state.totq else "💀 Over")
    points.button(f'Pts: {st.session_state.points}')

 

if __name__ == "__main__":
    main()
    footer()