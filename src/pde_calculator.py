import requests

from openai import OpenAI

import json
import re

import logger
import logging

from Extractor import Extractor


logger.init()


def calculate_pde(substance_name):

    F1 = F2 = F3 = F4 = F5 = 1  


    ex = Extractor(substance_name)
    data = ex.data 

    logging.debug(f"{substance_name = }")

    # Dictionary to string
    text = json.dumps(data)
    
    prompt_teamplate = '''I will give you a text and you will anwser only with the following information in a programming friendly way: 

    -Animal; 
    -Study duration time; 
    -Type of toxicity; 
    -LD50, or LOAEL,or NOAEL,or NOEL, or LOEL. 
    
    
    Write like this Example:

    Animal: Rat, Mouse
    Study duration time: Not specified
    Type of toxicity: Acute toxic effects, specifically oral, intraperitoneal, and subcutaneous routes.
    LD50 values:
        - Rat oral LD50: 2400 mg/kg
        - Rat intraperitoneal LD50: 1205 mg/kg
        - Mouse oral LD50: 338 mg/kg
        - Mouse intraperitoneal LD50: 367 mg/kg
        - Mouse subcutaneous LD50: 310 mg/kg

    
    '''
    #dictionary to string
    text = json.dumps(data)


    prompt = f"{prompt_teamplate} + {text}"

    api_key = "REMOVED"

    client = OpenAI(api_key= api_key)

    completion = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": prompt_teamplate},
            {"role": "user", "content": text}
        ]
    )

    completion_text = completion.choices[0].message.content

    extracted_info = extract_info(completion_text)
    effective_dose_value = extracted_info.get('effective_dose_value')
    W = 50
    F1 = determine_F1(extracted_info['animal_str'])
    F2 = 10
    F3 = determine_F3(extracted_info['duration_weeks'], extracted_info['animal_str'])
    F4 = determine_F4(extracted_info['neurotoxicity'], extracted_info['carcinogenicity'], extracted_info['teratogenicity'], extracted_info['unknown_toxicity'])
    F5 = determine_F5(extracted_info['effect_type'])
    PDE = (effective_dose_value * W)/(F1 * F2 * F3 * F4 * F5)

    return {
        'pde': PDE,
        'effective_dose_value': effective_dose_value,
        'f1': F1,
        'f2': F2,
        'f3': F3,
        'f4': F4,
        'f5': F5

    }

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

    # Padrão atualizado para lidar com diferentes formatos e variações
    pattern = r'(\bLD50|\bLOAEL|\bNOAEL|\bNOEL)\s*[^:]*:\s*(?:>|about|approx\.)*\s*([\d.]+)\s*mg/kg'

    lowest_value = None
    effect_type = None

    # Buscar todas as correspondências
    matches = re.findall(pattern, completion_text, re.IGNORECASE)
    for match in matches:
        # Converter o valor capturado em um número decimal
        value = float(match[1])
        if lowest_value is None or value < lowest_value:
            lowest_value = value
            effect_type = match[0].upper()  # Padronizar para maiúsculas
        

    return {
        'animal_str': animal_str,
        'duration_weeks': duration_weeks,
        'neurotoxicity': neurotoxicity,
        'carcinogenicity': carcinogenicity, 
        'teratogenicity': teratogenicity,
        'unknown_toxicity': unknown_toxicity,
        'effect_type': effect_type,
        'effect_level': effect_level,
        'ld50': ld50,
        'loael': loael,
        'noael': noael,
        'noel': noel,
        'effective_dose_value': lowest_value
    }

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

def determine_F5(effect_type):
    if effect_type.lower() in ["noael", "noel", "ld50"]:
        return 1
    elif effect_type.lower() == "loael":
        return min(determine_F4(), 5)
    else:
        return 10


