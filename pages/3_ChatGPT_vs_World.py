import pandas as pd
import re
import time
import os

import streamlit as st
import requests
import json
from footer import footer
from utils import *

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools, initialize_agent
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.callbacks import StreamlitCallbackHandler
from langchain.callbacks import get_openai_callback

os.environ["WOLFRAM_ALPHA_APPID"] = "ULLYPR-PVA7XY3Y89"
llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0, streaming=True)
tools = load_tools(["serpapi", "wolfram-alpha"], llm=llm) 

# Finally, let's initialize an agent with the tools, the language model, and the type of agent we want to use.
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)
callback_properties = [
        "total_tokens",
        "prompt_tokens",
        "completion_tokens",
        "total_cost",
]

def init(heart: int = 3, 
         qsource: str = "Archive",
         theme: str = "General",
         post_init = False):
    if not post_init:
        # Used to prevent "please make a guess" warning when starting a brand new session
        st.session_state.start = 0  
        # Distinguish between a brand new session and restart
        st.session_state.input = 0
        # Track number of points scored in a game
        st.session_state.points = 0
        # Track number of lives remaining
        st.session_state.heart = heart
        # Track total number of questions received in a game
        st.session_state.nq = 0
        # Track number of questions answered correctly in a game
        st.session_state.answered = 0
        # Track question source
        st.session_state.qsource = qsource
        # Track question theme
        st.session_state.theme = theme

    st.session_state.start = 0
    st.session_state.question = generate_question_from_archive(None, None)
    st.session_state.lives = heart


def restart():
    init(st.session_state.lives,
         st.session_state.qsource,
         st.session_state.theme,
         post_init=True)
    st.session_state.input += 1
    st.session_state.points = 0
    st.session_state.heart = 3
    st.session_state.lives = 3


def main():
    
    st.title("This is Jeopardy!")
    st.write("##### **Contestant asks, ChatGPT responds**")
    st.write("")

    if 'question' not in st.session_state:
        init()

    p1, p2, p3, b1, b2, response, debug = st.empty(), st.empty(), st.empty(), st.empty(), st.empty(), st.empty(), st.empty()

    category = p1.text_input("**Category:**")
    question = p2.text_input("**Clue:**")
    value = p3.text_input("**Points:**", 1000)
    b1.write("")
    go = b2.button("Go ChatGPT!")

    if go: 
        with get_openai_callback() as cb:
            prompt = f"This is Jeopardy! The category is {category}. The clue is \"{question}\". You can perform any necessary calculations to get the answer. You should answer in as few words as possible. You will only provide the answer, you will not respond in the form of a question"
            st_callback = StreamlitCallbackHandler(st.container())
            response = agent.run(prompt, callbacks=[st_callback])
            st.write(response)
            st.markdown(f"**Usage:**")
            cb_dict = {}
            for prop in callback_properties:
                value = getattr(cb, prop, 0)
                cb_dict[prop] = value
            st.write(cb_dict)
            

if __name__ == "__main__":
    main()
    footer()