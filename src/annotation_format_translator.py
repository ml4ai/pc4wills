import json
import argparse

"""
This program is for switching the format of the legal will dataset introduced by Kwak et al. (2023) into the one used by our project. To download the dataset, visit: https://github.com/ml4ai/ie4wills/tree/main/data/raw. To run this program, run the following code: python format_translator.py path/to/your/input_file.json path/to/your/output_path
"""

def main():
  # get the path to the input file as an argument
  parser = argparse.ArgumentParser(description='Process some data.')
  parser.add_argument('input_file', type=str, help='Path to the input file')
  parser.add_argument('output_path', type=str, help='Path to save the output files')
  args = parser.parse_args()
  file = args.input_file
  output_path = args.output_path

  with open(file) as f:
    data = json.load(f)

  for datum in data:
    # take care of entities
    entity_dict = get_entity_dictionary(datum['annotations'][0]['result'])
    id_dict, entity_json_list = switch_entity_to_json(entity_dict, datum['annotations'][0]['result'])

    # take care of events
    event_list = handling_events(datum['annotations'][0]['result'], id_dict, entity_dict)
    id_trigger_type, new_event_dict_list = event_to_json_list(event_list)
    event_json_list = change_trigger_to_event(id_trigger_type, new_event_dict_list)

    # make into json format
    final_json = {"text": datum['data']['text'], "entities": entity_json_list, "events": event_json_list}

    # Serializing json
    json_object = json.dumps(final_json, indent=4)
    json_file_name = output_path+"/"+str(datum['id'])+".json"

    # Writing to sample.json
    with open(json_file_name, "w") as outfile:
        outfile.write(json_object)

def merge_overlapping_lists(lists):
    merged = []
    while lists:
        current_list = lists.pop(0)
        i = 0
        while i < len(merged):
            if any(item in merged[i] for item in current_list):
                current_list.extend(merged.pop(i))
                i = 0  # Start over after merging
            else:
                i += 1
        merged.append(list(set(current_list)))
    return merged

def count_keys_starting_with_entity(dictionary, entity):
    count = 0
    for key in dictionary.keys():
        if key.startswith(entity):
            count += 1
    return count

def id_into_text(entities, data):
  text_entities = []
  for entity in entities:
    for i in data:
      if i.get('id') == entity and i['value']['text'].strip() not in text_entities:
        text_entities.append(i['value']['text'].strip())
  return text_entities

def get_entity_dictionary(data):
  entire_entities = []
  for item in data:
    if item.get('id'):
      entire_entities.append([item.get('id')])
    if item.get('labels') == ["COREFERENCE_RESOLUTION"]:
      entire_entities.append([item['from_id'], item['to_id']])

  # merge any lists that contains overlapping entity (this will handle coreference resolution)
  coreference_resolution = merge_overlapping_lists(entire_entities)

  # get rid of any redundant entities from merged lists
  for i in coreference_resolution:
    i = list(set(i))

  # make the list into dictionary by adding the labels for each list
  final_entities = {}
  for i in coreference_resolution:
    for j in data:
      if j.get('id') == i[0]:
        count = count_keys_starting_with_entity(final_entities, j['value']['labels'][0])
        final_entities[j['value']['labels'][0]+str(count+1)] = i

  return final_entities

def switch_entity_to_json(final_entities, data):
  entity_list = []
  id_dict = {}
  for entity in final_entities:
    if entity.startswith("TRIGGER") == False:
      entity_json = {}
      id = "e"+str(len(entity_list)+1)
      entity_json["id"] = id
      entity_json["texts"] = id_into_text(final_entities[entity], data)
      entity_type = entity.replace("_", " ").lower().title().replace(" ", "")
      final_entity = ''.join([i for i in entity_type if not i.isdigit()])
      entity_json["type"] = final_entity
      entity_list.append(entity_json)
      id_dict[id] = final_entities[entity]
  return id_dict, entity_list

# start handling events
def handling_events(data, id_dict, entity_dict):
  result_dict = {}
  for datum in data:
    if datum.get('type') == 'relation':
      if len(datum['labels']) != 0:
        if datum['labels'][0] != 'COREFERENCE_RESOLUTION':
          labels = datum['labels']
          from_id = datum['from_id']
          to_id = datum['to_id']
          if check_if_event(from_id, data):
            for label in labels:
              key = (label, from_id)
              if key not in result_dict:
                  result_dict[key] = []
              result_dict[key].append(to_id)
      else:
        print("no relation label, need to check:", datum)

  # change the format of the dict (merge args by events)
  new_dict_list = []
  for key, value in result_dict.items():
      type_args = {}
      for i in entity_dict:
        for v in value:
          if v in entity_dict[i]:
            if key not in type_args:
              type_args[key] = [(i, entity_dict[i])]
            else:
              type_args[key].append((i, entity_dict[i]))
      if type_args != {}:
        new_dict_list.append(type_args)

  final_list = []
  for event_dict in new_dict_list:
    for i in event_dict:
      new_list = []
      for j in event_dict[i]:
        j = list(j)
        j[1] = annotation_id_to_json_id(j[1], id_dict)
        new_list.append(j)
      event_dict[i] = new_list
    final_list.append(event_dict)

  return final_list

def check_if_event(id, data):
  for datum in data:
    if datum.get('id') == id:
      return datum['value']['labels'] == ['TRIGGER']

def annotation_id_to_json_id(annotation_id_list, id_dict):
  new_id = annotation_id_list
  for id in id_dict:
    if annotation_id_list == id_dict[id]:
      new_id = id
  return new_id

def event_to_json_list(final_list):
  new_event_dict_list = []
  id_trigger_type_list = []
  for item in final_list:
    for key, value in item.items():
      new_event_dict = {}
      id_trigger_type = {}
      new_event_dict['id'] = "v"+str(len(new_event_dict_list)+1)
      key_to_type = key[0].replace("_", " ").lower().title()
      new_event_dict['type'] = key_to_type.replace(" ", "")
      id_trigger_type["v"+str(len(new_event_dict_list)+1)] = (key[1], key_to_type.replace(" ", ""))
      for string in value:
        modified_string = ''.join([i for i in string[0] if not i.isdigit()])
        arg_name = modified_string.replace("_", " ").lower().title().replace(" ", "")
        if arg_name not in new_event_dict.keys():
          new_event_dict[arg_name] = [string[1]]
        else:
          new_event_dict[arg_name].append(string[1])
      new_event_dict_list.append(new_event_dict)
      id_trigger_type_list.append(id_trigger_type)

  return id_trigger_type_list, new_event_dict_list

def change_trigger_to_event(id_trigger_type, new_event_dict_list):
  final_event_list = []
  for event_dict in new_event_dict_list:
    new_event_dict = {}
    for k, v in event_dict.items():
      if isinstance(v[0], list):
        for each_dict in id_trigger_type:
          for i in each_dict:
            if v[0][0] == each_dict[i][0]:
              if each_dict[i][1] not in new_event_dict.keys():
                new_event_dict[each_dict[i][1]] = [i]
              else:
                new_event_dict[each_dict[i][1]].append(i)
      else:
        new_event_dict[k] = v
    final_event_list.append(new_event_dict)
  return final_event_list

if __name__ == "__main__":
  main()