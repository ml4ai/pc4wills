import json, os
import random


# open all the files in the directory and save them in a dict
def read_json_files(directory):
    json_data = {}
    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):  # Check if file is a JSON file
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                try:
                    data = json.load(file)
                    json_data[filename] = data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file '{filename}': {e}")
    return json_data


# Loop through the list and sort by event type
def make_example_pool(json_data):
    # define the event types
    events = ["WillCreation", "Direction", "Bequest", "Nomination", "SignWill", "Attestation", "Authorization", "Revocation", "Excuse"]
    sort_by_type = {}
    for k, v in json_data.items():
        event_sorted = False
        for e in v['events']:
            for event in events:               
                if e['type'] == event:    
                    if event in sort_by_type and (k, v) not in sort_by_type[event]:
                        event_sorted = True
                        sort_by_type[event].append((k, v))
                    elif event not in sort_by_type:
                        event_sorted = True
                        sort_by_type[event] = [(k, v)]
        if event_sorted == False:
            if 'Etc' not in sort_by_type:
                sort_by_type['Etc'] = [(k, v)]
            else:
                sort_by_type['Etc'].append((k, v))
    return sort_by_type


# Method selecting a random number => use the example with the index as a demo (attach to a list and return the list)
def select_random_example(example_pool, num_of_example):
    selected_examples = []
    random_int = random.sample(range(0, len(example_pool)), int(num_of_example))
    for i in random_int:
        random_example = example_pool[i]
        selected_examples.append(random_example)
    return selected_examples


def create_example_list(full_example_pool, classification, num_of_example):
    events = ["WillCreation", "Direction", "Bequest", "Nomination", "SignWill", "Attestation", "Authorization", "Revocation", "Excuse"]
    example_list = []
    n = 0
    while n < len(classification):
        if classification[n] == 1:
            example_pool = full_example_pool[events[n]]
            selected_examples = select_random_example(example_pool, num_of_example)
            example_list += selected_examples
        n += 1
    if len(example_list) == 0:
        example_pool = full_example_pool['Etc']
        selected_examples = select_random_example(example_pool, num_of_example)
        example_list += selected_examples
    return example_list


def create_full_prompt(example_list):
    first_part = """Your task is to extract all instances of the following entities and events (including pronouns) from the will texts and output the extraction in JSON format.

%entities: Testator, Beneficiary, Witness, State, County, Asset, Bond, Executor, Date, Time, Trustee, Will, Codicil, Debt, Expense, Tax, Duty, Right, Condition, Guardian, Trust, Conservator, Affidavit, NotaryPublic, NonBeneficiary
%events: WillCreation, SignWill, Attestation, Revocation, Codicil, Bequest, Nomination, Disqualification, Renunciation, Death, Probate, Direction, Authorization, Excuse, Give, Notarization, NonProbateInstrumentCreation, Birth, Residual, Removal

Here’s some examples of expected outputs in the desired format.

"""
    example_ids = []
    prompt_examples = []
    for example in example_list:
        example_ids.append(example[0])
        prompt_examples.append(json.dumps(example[1], indent=4))
    full_demo = ',\n'.join(prompt_examples)
    full_prompt = first_part + full_demo
    return full_prompt, example_ids


def main(directory, classification=[1, 1, 1, 1, 1, 1, 1, 1, 1], num_of_example=1):
    json_data = read_json_files(directory)
    example_pool = make_example_pool(json_data)
    example_list = create_example_list(example_pool, classification, num_of_example)
    full_prompt, example_ids = create_full_prompt(example_list)
    return full_prompt