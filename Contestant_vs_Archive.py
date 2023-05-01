import pandas as pd
import re
import time
import os

import streamlit as st
import requests
import json
from footer import footer

### https://gist.github.com/scotta/1063364
### based on: http://www.catalysoft.com/articles/StrikeAMatch.html
### similar projects: https://pypi.org/project/Fuzzy/
### another good article: https://medium.com/@yash_agarwal2/soundex-and-levenshtein-distance-in-python-8b4b56542e9e

def _get_character_pairs(text):
    """Returns a defaultdict(int) of adjacent character pair counts.
    >>> _get_character_pairs('Test is')
    {'IS': 1, 'TE': 1, 'ES': 1, 'ST': 1}
    >>> _get_character_pairs('Test 123')
    {'23': 1, '12': 1, 'TE': 1, 'ES': 1, 'ST': 1}
    >>> _get_character_pairs('Test TEST')
    {'TE': 2, 'ES': 2, 'ST': 2}
    >>> _get_character_pairs('ai a al a')
    {'AI': 1, 'AL': 1}
    >>> _get_character_pairs('12345')
    {'34': 1, '12': 1, '45': 1, '23': 1}
    >>> _get_character_pairs('A')
    {}
    >>> _get_character_pairs('A B')
    {}
    >>> _get_character_pairs(123)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "strikeamatch.py", line 31, in _get_character_pairs
        if not hasattr(text, "upper"): raise ValueError
    ValueError: Invalid argument
    """

    if not hasattr(text, "upper"):
        raise ValueError("Invalid argument")

    results = dict()

    for word in text.upper().split():
        for pair in [word[i]+word[i+1] for i in range(len(word)-1)]:
            if pair in results:
                results[pair] += 1
            else:
                results[pair] = 1
    return results

def compare_strings(string1, string2):
    """Returns a value between 0.0 and 1.0 indicating the similarity between the
    two strings. A value of 1.0 is a perfect match and 0.0 is no similarity.
    >>> for w in ('Sealed', 'Healthy', 'Heard', 'Herded', 'Help', 'Sold'):
    ...     compare_strings('Healed', w)
    ... 
    0.8
    0.5454545454545454
    0.4444444444444444
    0.4
    0.25
    0.0
    >>> compare_strings("Horse", "Horse box")
    0.8
    >>> compare_strings("Horse BOX", "Horse box")
    1.0
    >>> compare_strings("ABCD", "AB") == compare_strings("AB", "ABCD") 
    True
    
    """
    s1_pairs = _get_character_pairs(string1)
    s2_pairs = _get_character_pairs(string2)

    s1_size = sum(s1_pairs.values())
    s2_size = sum(s2_pairs.values())

    intersection_count = 0

    # determine the smallest dict to optimise the calculation of the
    # intersection.
    if s1_size < s2_size:
        smaller_dict = s1_pairs
        larger_dict = s2_pairs
    else:
        smaller_dict = s2_pairs
        larger_dict = s1_pairs

    # determine the intersection by counting the subtractions we make from both
    # dicts.
    for pair, smaller_pair_count in smaller_dict.items():
        if pair in larger_dict and larger_dict[pair] > 0:
            if smaller_pair_count < larger_dict[pair]:
                intersection_count += smaller_pair_count
            else:
                intersection_count += larger_dict[pair]

    return (2.0 * intersection_count) / (s1_size + s2_size)


def sanitize(string):
    string = re.sub(r"/[^\w\s]/i", "", string)
    string = re.sub(r"\([^()]*\)", "", string)
    string = re.sub(r"/^(the|a|an) /i", "", string)
    string = string.strip().lower()
    return string


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


def init(heart: int = 3, 
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

    st.session_state.start = 0
    st.session_state.question = get_random_question_from_cluebase(None, None)
    st.session_state.lives = heart


def restart():
    init(st.session_state.lives,
         post_init=True)
    st.session_state.input += 1


def main():

    st.title("This is Jeopardy!")
    st.write("##### **Contestant responds to questions from JArchive**")
    st.write("")

    if 'question' not in st.session_state:
        init()

    reset, points, lives, settings = st.columns([2, 2, 2, 6], gap="small")
    reset.button(f'Reset', on_click=restart)

    with settings.expander('Settings'):
        st.select_slider('Set lives', list(range(1, 6)), 3, key='heart', on_change=restart)

    header1, header2, header3, placeholder, debug = st.empty(), st.empty(), st.empty(), st.empty(), st.empty()

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
        st.session_state.nq += 1
        prev_guess = guess
        sresponse = sanitize(guess)
        sanswer = sanitize(answer)
        sanswer = sanswer.split()[-1]
        if (compare_strings(sresponse, sanswer) >= 0.5):
            debug.success(f"**Correct**, the answer was: {answer}! 🎈")
            st.session_state.points += value
            st.session_state.answered += 1
            st.button('Next', on_click=restart)
        else:
            debug.error(f"**Incorrect**, the answer was: {answer}! 😓")
            st.session_state.points -= value
            st.session_state.lives -= 1
            if st.session_state.lives > 0:            
                st.button('Next', on_click=restart)

    if st.session_state.lives == 0:
        score = f"{st.session_state.points} ({st.session_state.answered}/{st.session_state.nq})"
        debug.error(f"**Incorrect**, the answer was: {answer}! **Sorry, Game Over** Your score: {score} 😓")
        st.button('Play again?', on_click=init)
        
    lives.button(f'{("❤️" * st.session_state.lives) if st.session_state.lives else "💀 Lost"}')
    points.button(f'🏆 {st.session_state.points}')

 

if __name__ == "__main__":
    main()
    footer()