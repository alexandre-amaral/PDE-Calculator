import requests

from openai import OpenAI

import json
import re

import logger
import logging

from extractorTest import Extractor


logger.init()

name = "paracetamol"
ex = Extractor(name)
tm = ex.tm
data = ex.data


logging.debug(f"{name = }")

prompt_teamplate = '''I will give you a text and you will anwser only with the following information in a programming friendly way: 

-Animal; 
-Study duration time; 
-Type of toxicity; 
-NOAEL, or LOAEL, or NOEL, or LD50, .

'''
 #dictionary to string
text = json.dumps(data)


prompt = f"{prompt_teamplate} + {text}"

import os

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

completion = client.chat.completions.create(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "system", "content": prompt_teamplate},
        {"role": "user", "content": text}
    ]
)

completion_text = completion.choices[0].message.content


def extract_info(completion_text):
    animal_str = ""
    duration_weeks = 0.0
    neurotoxicity = False
    carcinogenicity = False
    teratogenicity = False
    unknown_toxicity = False
    effect_type = ""
    effect_level = 0.0
    ld50 = None
    loael = None
    noael = None
    noel = None

    animal_match = re.search(r'Animal: ([\w\s,]+)', completion_text)
    if animal_match:
        animal_str = animal_match.group(1)
    if animal_str:
        animal_str = animal_str.split(',')[0].strip()

    duration_match = re.search(r'Study duration time: ([\w\s-]+)', completion_text)
    if duration_match:
        duration_str = duration_match.group(1)
        if duration_str == 'Long-term':
            duration_weeks = 52.0
        elif duration_str == 'Short-term':
            duration_weeks = 4.0

    toxicity_match = re.search(r'Type of toxicity: ([\w\s,-]+)', completion_text)
    if toxicity_match:
        toxicity_str = toxicity_match.group(1)
        if 'Neurotoxicity' in toxicity_str:
            neurotoxicity = True
        if 'Carcinogenicity' in toxicity_str:
            carcinogenicity = True
        if 'Teratogenicity' in toxicity_str:
            teratogenicity = True
        if 'Unknown' in toxicity_str:
            unknown_toxicity = True

    # Extraia valores de LD50, LOAEL, NOAEL, e NOEL
    ld50 = re.search(r'LD50: ([\w\s=,./()-]+)', completion_text).group(1) if re.search(r'LD50: ([\w\s=,./()-]+)', completion_text) else None
    loael = re.search(r'LOAEL: ([\w\s=,./()-]+)', completion_text).group(1) if re.search(r'LOAEL: ([\w\s=,./()-]+)', completion_text) else None
    noael = re.search(r'NOAEL: ([\w\s=,./()-]+)', completion_text).group(1) if re.search(r'NOAEL: ([\w\s=,./()-]+)', completion_text) else None
    noel = re.search(r'NOEL: ([\w\s=,./()-]+)', completion_text).group(1) if re.search(r'NOEL: ([\w\s=,./()-]+)', completion_text) else None

    # Determinar qual valor usar e extrair apenas o número
    effective_dose_value = None
    for value in [loael, noel, ld50, noael]:
        if value and value != 'Not specified':
            number_match = re.search(r'([\d.]+)', value)
            if number_match:
                effective_dose_value = float(number_match.group(1))
                break


    effect_match = re.search(r'(NOAEL|NOEL|LOAEL|LD50)\s*=\s*([\w\s=,./-]+)', completion_text)
    if effect_match:
        effect_type = effect_match.group(1)
        effect_level_str = effect_match.group(2)
        level_match = re.search(r'([\d.]+)', effect_level_str)
        if level_match:
            effect_level = float(level_match.group(1))
    

    return animal_str, duration_weeks, neurotoxicity, carcinogenicity, teratogenicity, unknown_toxicity, effect_type, effect_level, effective_dose_value

animal_str, duration_weeks, neurotoxicity, carcinogenicity, teratogenicity, unknown_toxicity, effect_type, effect_level, effective_dose_value = extract_info(completion_text)


def determine_F1(animal_str):
    animals = animal_str.lower().split(' and ')
    animal_values = []
    for animal in animals:
        if 'human' in animal:
            animal_values.append(1)
        elif 'dog' in animal:
            animal_values.append(2)
        elif 'rabbit' in animal:
            animal_values.append(2.5)
        elif 'monkey' in animal or 'chimp' in animal:
            animal_values.append(3)
        elif 'mouse' in animal:
            animal_values.append(12)
        elif 'rat' in animal:
            animal_values.append(5)
        else:
            pass
    if animal_values:
        return min(animal_values)
    else:
        return None

def determine_F3(duration_weeks, animal_str):
    half_life_years = {'rodent': 1, 'rabbit': 1, 'cat': 7, 'dog': 7, 'monkey': 7}
    if 'reproductive' in animal_str.lower() or 'organogenesis' in animal_str.lower():
        return 1
    elif duration_weeks >= 26 * half_life_years['rodent'] and 'rodent' in animal_str.lower():
        return 2
    elif duration_weeks >= 42 * half_life_years['cat'] and 'cat' in animal_str.lower():
        return 2
    elif duration_weeks >= 42 * half_life_years['dog'] and 'dog' in animal_str.lower():
        return 2
    elif duration_weeks >= 42 * half_life_years['monkey'] and 'monkey' in animal_str.lower():
        return 2
    elif duration_weeks >= 13 * half_life_years['rodent'] and 'rodent' in animal_str.lower():
        return 5
    elif duration_weeks >= 24 * half_life_years['cat'] and 'cat' in animal_str.lower():
        return 5
    elif duration_weeks >= 24 * half_life_years['dog'] and 'dog' in animal_str.lower():
        return 5
    elif duration_weeks >= 24 * half_life_years['monkey'] and 'monkey' in animal_str.lower():
        return 5
    else:
        return 10


def determine_F4(neurotoxicity, carcinogenicity, teratogenicity, unknown_toxicity):
    if teratogenicity and not unknown_toxicity and neurotoxicity:
        return 5
    elif teratogenicity and not unknown_toxicity:
        return 10
    elif neurotoxicity and not teratogenicity and not carcinogenicity and not unknown_toxicity:
        return 5
    else:   
        return 1

def determine_F5(effect_level_type):
    if effect_level_type in ["NOAEL", "NOEL," ,"LD50"]:
        return 1
    elif effect_level_type == "LOAEL":
        return min(determine_F4(), 5)
    else:
        return 10
    
F1 = determine_F1(animal_str)
F2 = 10
F3 = determine_F3(duration_weeks, animal_str)
F4 = determine_F4(neurotoxicity, carcinogenicity, teratogenicity, unknown_toxicity)
F5 = determine_F5(effect_type)
W = 50


#save LD50, LOAEL, NOAEL or LOEL in a variable
 


def determine_PDE(F1, F2, F3, F4, F5):
    PDE = (effective_dose_value * W)/(F1 * F2 * F3 * F4 * F5)
    return PDE


PDE = determine_PDE(F1, F2, F3, F4, F5)


print(completion_text)
print("PDE = ", PDE) 
print("F1 = ", F1)
print("F2 = ", F2)
print("F3 = ", F3)
print("F4 = ", F4)
print("F5 = ", F5)
print("LD50 or LOAEL or NOAEL or NOEL = ", effective_dose_value)