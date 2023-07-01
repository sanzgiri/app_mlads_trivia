import requests
import json
import re
import random

### https://gist.github.com/scotta/1063364
### based on: http://www.catalysoft.com/articles/StrikeAMatch.html
### similar projects: https://pypi.org/project/Fuzzy/
### another good article: https://medium.com/@yash_agarwal2/soundex-and-levenshtein-distance-in-python-8b4b56542e9e

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

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


def generate_question_from_archive(difficulty, category):

  if category is not None:
     url = f"http://cluebase.lukelav.in/clues/random?category='{category}'"
  elif difficulty is not None:
    url = f"http://cluebase.lukelav.in/clues/random?difficulty='{difficulty}'"
  else:
    url = "http://cluebase.lukelav.in/clues/random"
    
  response = requests.get(url)
  data = json.loads(response.text)
  print(url, data)
  if len(data['data']) == 0:
    print("No questions found")
    return []
  else:
    clue = data['data'][0]['clue']
    category = data['data'][0]['category']
    true_answer = data['data'][0]['response']
    value = 1000
    return [category, clue, true_answer, value]


def get_jeopardy_response_from_llm_no_chain(category, clue):

  prompt = f"This is Jeopardy! The category is {category}. The clue is \"{clue}\". You can perform any necessary calculations to get the answer. You should answer in as few words as possible. You will only provide the answer, you will not respond in the form of a question."
  return llm(prompt)


def get_jeopardy_response_from_llm_with_chain(category, clue):

    prompt = f"This is Jeopardy! The category is {category}. The clue is \"{clue}\". You can perform any necessary calculations to get the answer. You will not respond in the form of a question!"

    return agent.run(prompt)


def generate_question_from_chatgpt(difficulty, category):

  if category is None:
    if difficulty is None:
      prompt = f"""This is Jeopardy!
Generate a tough trivia question worth {random.randrange(1,5)*200} points.
You should know the answer to the question you are asking.
Provide the question, category, points and correct answer in python dictionary format.
Do not specify the correct answer in the form of a question!
"""
    else:
      prompt = f"""This is Jeopardy!
Generate a question from a random category and difficulty level {difficulty}. 
Difficuly levels range from 1-5 with 1 being most easy and 5 being most difficult.
Points are 200 times the difficulty level. 
Provide the question, category, points and correct answer in python dictionary format.
"""
  else:
    if difficulty is None:
      prompt =  f"""This is Jeopardy!
Generate a question from category {category} and a random difficulty level. 
Difficuly levels range from 1-5 with 1 being most easy and 5 being most difficult.
Points are 200 times the difficulty level. 
Provide the question, category, points and correct answer in python dictionary format.
"""
    else:
      prompt =  f"""This is Jeopardy!
Generate a question from category {category} and difficulty level {difficulty}. 
Difficuly levels range from 1-5 with 1 being most easy and 5 being most difficult.
Points are 200 times the difficulty level. 
Provide the question, category, points and correct answer in python dictionary format.
"""
  
  response = llm(prompt)
  res_dict = json.loads(response)
  return [res_dict["category"], res_dict["question"], res_dict["answer"], res_dict["points"]]
