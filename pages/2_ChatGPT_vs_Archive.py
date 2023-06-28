import pandas as pd
import re
import os
import sys

sys.path.append(os.path.abspath('..'))
from utils import *

import streamlit as st
import requests
import json
from footer import footer

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools, initialize_agent
from langchain.chains.conversation.memory import ConversationBufferMemory

llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)
tools = load_tools(["serpapi"], llm=llm) 

# Finally, let's initialize an agent with the tools, the language model, and the type of agent we want to use.
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

async def run_agent(prompt):
    return agent.run(prompt)



def get_jeopardy_response_from_llm_no_chain(category, clue):

  prompt = f"This is Jeopardy! The category is {category}. The clue is \"{clue}\". You can perform any necessary calculations to get the answer. Do not respond in the form of a question!"
  return llm(prompt)


def get_jeopardy_response_from_llm_with_chain(category, clue):

  prompt = f"This is Jeopardy! The category is {category}. The clue is \"{clue}\". You can perform any necessary calculations to get the answer. Do not respond in the form of a question!"
  return agent.run(prompt)


def get_random_question_from_cluebase(difficulty, category):

  if difficulty is None:
      difficulty = 5

  if category is not None:
    url = f"http://cluebase.lukelav.in/clues/random?category='{category}'&difficulty={int(difficulty)}"
  else:
    url = f"http://cluebase.lukelav.in/clues/random?difficulty={int(difficulty)}"

  response = requests.get(url)
  data = json.loads(response.text)
  print(url, data)
  clue = data['data'][0]['clue']
  category = data['data'][0]['category']
  true_answer = data['data'][0]['response']
  value = difficulty*200
  return [category, clue, true_answer, value]


def init(totq: int = 3, 
         theme: str = "General",
         explain: bool = 0,
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
        # Track question theme
        st.session_state.theme = theme
        # Track chatgpt explanation
        st.session_state.explain = explain

    st.session_state.start = 0
    st.session_state.question = get_random_question_from_cluebase(None, st.session_state.theme)
    st.session_state.totq = totq


def restart():
    init(st.session_state.totq,
         st.session_state.theme,
         st.session_state.explain,
         post_init=True)
    st.session_state.input += 1


def main():
    
    st.title("This is Jeopardy!")
    st.write("##### **Archive asks, ChatGPT responds**")
    st.write("")

    if 'question' not in st.session_state:
        init()

    reset, points, questions, settings = st.columns([2, 2, 2, 6], gap="small")
    reset.button(f'Reset', on_click=restart)

    with settings.expander('Settings'):
        theme = st.selectbox("Theme", ("Before and After", "Events after Sep 2021", "Movie Mashups", "C"), key='theme')
        st.select_slider('Set lives', list(range(1, 6)), 3, key='heart', on_change=restart)
        explain = st.radio("Show ChatGPT Reasoning", (0, 1), key='explain', horizontal=True)

    header1, header2, header3, placeholder, response, debug = st.empty(), st.empty(), st.empty(), st.empty(), st.empty(), st.empty()

    category = st.session_state.question[0]
    question = st.session_state.question[1]
    answer = st.session_state.question[2]
    value = st.session_state.question[3]

    header1.write(f"**Category:** {category}")
    header2.write(f"**Clue:** {question}")
    header3.write(f"**Points:** {value}")

    go = placeholder.button("Go ChatGPT!")

    if go: 
        if st.session_state.explain == 0:
            guess = get_jeopardy_response_from_llm_no_chain(category, question)
        else:
            #guess = get_jeopardy_response_from_llm_with_chain(category, question)
            prompt = f"This is Jeopardy! The category is {category}. The clue is \"{question}\". You can perform any necessary calculations to get the answer. Do not respond in the form of a question!"
            guess = agent.run(prompt)
        response.write(f"ChatGPT response: {guess}")
            
        guess = guess.lower()
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
        debug.error(f"**Incorrect**, the answer was: {answer}! **Sorry, Game Over** Your score: {score} 😓")
        st.button('Play again?', on_click=init)
    
    questions.button(f'Q: {st.session_state.nq}' if st.session_state.nq <= st.session_state.totq else "💀 Over")
    points.button(f'Pts: {st.session_state.points}')


 

if __name__ == "__main__":
    main()
    footer()