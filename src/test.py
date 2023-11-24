import requests

from openai import OpenAI

import json
import re

import logger
import logging

from Extractor import Extractor


ex = Extractor("loratadine")
data = ex.data 

    

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

extracted_info = extract_info(completion_text)
effective_dose_value = extracted_info.get('effective_dose_value')
print (completion_text)
print(effective_dose_value)