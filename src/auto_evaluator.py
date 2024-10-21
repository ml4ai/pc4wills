import json
import os
import csv
import difflib
import argparse

"""
This program is for evaluating the LLM's outputs automatically by comparing them with gold data. This evaluator uses a default similarity threshold of 0.7, which can be adjusted at line 236. To make the evaluation more stringent, increase the threshold; for a more flexible evaluation, decrease it. To run the program, run the following code: 
```
python auto_evaluator.py path/to/your/gold_files path/to/your/pred_files path/to/your/output "gold_file_name" "pred_file_name"
```
"""

def main():
    parser = argparse.ArgumentParser(description='Process some data.')
    parser.add_argument('gold_path', type=str, help='Path to the gold files')
    parser.add_argument('pred_path', type=str, help='Path to the prediction files')
    parser.add_argument('output_path', type=str, help='Path to the output file')
    parser.add_argument('gold_name', type=str, help='Name of the gold files')
    parser.add_argument('pred_name', type=str, help='Name of the prediction files')
    args = parser.parse_args()
    gold_path = args.gold_path
    pred_path = args.pred_path
    output_path = args.output_path
    gold_name = args.gold_name
    pred_name = args.pred_name

    total_evaluation(gold_path, pred_path, output_path, gold_name, pred_name)
    
# Function to calculate similarity between entity dictionaries (only considering "type" and "texts" fields)
def calculate_similarity(dict1, dict2, entity_or_event):
    if entity_or_event == "entity":
        # Compute the similarity for "type" field (1 if equal, 0 otherwise)
        type_similarity = 1 if dict1["type"] == dict2["type"] else 0

        # Calculate the text similarity as the average similarity of "texts" pairs
        text_similarity = sum(
            difflib.SequenceMatcher(None, text1, text2).ratio()
            for text1 in dict1["texts"]
            for text2 in dict2["texts"]
        ) / (len(dict1["texts"]) * len(dict2["texts"])) if (len(dict1["texts"]) * len(dict2["texts"])) > 0 else 0

        # Normalize text similarity to be between 0 and 1
        text_similarity = min(1.0, text_similarity)

        # Calculate an overall similarity score with a weighted combination
        overall_similarity = 0.7 * type_similarity + 0.3 * text_similarity

    elif entity_or_event == "event":
        similar = 0
        dissimilar = 0
        # Get the keys present in both dictionaries
        total_keys_set = set(dict1.keys()).union(dict2.keys())

        for key in total_keys_set:
            if key not in dict1:
                dissimilar += len(dict2[key])
            if key not in dict2:
                dissimilar += len(dict1[key])
            elif key in dict1 and key in dict2 and key != "id":
                total_values = set(dict1[key]).union(dict2[key])
                common_values = set(dict1[key]).intersection(dict2[key])
                similar += len(common_values)
                dissimilar += len(total_values) - len(common_values)

        overall_similarity = (similar / (similar + dissimilar))

    return overall_similarity

# Function to find best matches among entity dictionaries
def find_best_matches_among_dicts(dict_list1, dict_list2, entity_or_event):
    if not dict_list1 or not dict_list2:
        return [], {}

    best_matches = []

    while dict_list1 and dict_list2:
        best_match, best_similarity, best_index1, best_index2 = None, 0, None, None

        for index1, dict1 in enumerate(dict_list1):
            for index2, dict2 in enumerate(dict_list2):
                current_similarity = calculate_similarity(dict1, dict2, entity_or_event)

                if current_similarity > best_similarity:
                    best_match, best_similarity, best_index1, best_index2 = dict2, current_similarity, index1, index2

        if best_match is not None:
            best_matches.append((dict_list1[best_index1], best_match, best_similarity))
            dict_list1.pop(best_index1)
            dict_list2.pop(best_index2)

        elif (len(dict_list1) == 1 or len(dict_list2) == 1) and best_match is None:
            best_matches.append((dict_list1[0], dict_list2[0], 0))
            dict_list1.pop()
            dict_list2.pop()

    id_map = {}
    for matches in best_matches:
        id_map[matches[1]['id']] = matches[0]['id']

    return best_matches, id_map

# Function for finding best matching entities from "texts" lists in matching dictionaries
def find_best_matches_in_list(list1, list2):
    if not list1 or not list2:
        return []

    best_matches = []
    used_indices_list1 = set()
    used_indices_list2 = set()

    for _ in range(min(len(list1), len(list2))):
        best_match, best_similarity, best_index1, best_index2 = None, 0, None, None

        for index1, item1 in enumerate(list1):
            if index1 in used_indices_list1:
                continue

            for index2, item2 in enumerate(list2):
                if index2 in used_indices_list2:
                    continue

                # Compute the similarity ratio between item1 and item2
                seq_matcher = difflib.SequenceMatcher(None, item1, item2)
                current_similarity = seq_matcher.ratio()

                if current_similarity > best_similarity:
                    best_match, best_similarity, best_index1, best_index2 = item2, current_similarity, index1, index2

        if best_match is not None:
            best_matches.append((list1[best_index1], best_match, best_similarity))
            used_indices_list1.add(best_index1)
            used_indices_list2.add(best_index2)

    return best_matches

# Function for mapping ids from prediction to ids from golden
def mapping_ids(prediction_events, id_map):
  for args in prediction_events:
      for k, v in args.items():
        if isinstance(v, list):
          n = 0
          for id in v:
            for pred_id in id_map:
              if pred_id == id:
                v[n] = id_map[pred_id]
            n += 1
  return prediction_events

# Function for grouping event dicts by their types
def group_dictionaries_by_type(dictionaries):
    # Initialize a dictionary to store groups by "type" value
    type_groups = {}

    # Iterate through the dictionaries
    for dictionary in dictionaries:
        # Get the "type" value from the current dictionary
        type_value = dictionary.get("type")

        if type_value is not None:
            # Check if the type_value is already a key in type_groups
            if type_value in type_groups:
                # Append the current dictionary to the existing group
                type_groups[type_value].append(dictionary)
            else:
                # Create a new group for this type_value and add the current dictionary
                type_groups[type_value] = [dictionary]

    return type_groups

def counting_dict_for_each_type(golden_group, prediction_group):
    dict_for_counting = {}
    for types, dicts in golden_group.items():
        if prediction_group.get(types) is not None:
            dict_for_counting[types] = {"golden": len(golden_group[types]), "prediction": len(prediction_group[types])}
        else:
            dict_for_counting[types] = {"golden": len(golden_group[types]), "prediction": 0}

    for types, dicts in prediction_group.items():
        if types not in dict_for_counting.keys():
            dict_for_counting[types] = {"golden": 0, "prediction": len(prediction_group[types])}

    return dict_for_counting

# Function for comparing event type when it's one-to-one match.
def one_to_one_match_event(golden_event, prediction_event):
  similarity = 0
  dissimilarity = 0
  for k, v in golden_event.items():
    if k != 'id' and k != 'type' and k in prediction_event.keys():
      for id in v:
        if id in prediction_event[k]:
          similarity += 2
        if id not in prediction_event[k]:
          dissimilarity += 1
    if k != 'id' and k != 'type' and k not in prediction_event.keys():
      for id in v:
        dissimilarity += 1
  for k, v in prediction_event.items():
    if k != 'id' and k != 'type' and k in golden_event.keys():
      for id in v:
        if id not in golden_event[k]:
          dissimilarity += 1
    if k != 'id' and k != 'type' and k not in golden_event.keys():
      for id in v:
        dissimilarity += 1
  final_similarity = similarity / (similarity + dissimilarity)
  return final_similarity

# Function to read and parse a JSON file
def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {file_path}: {e}")
        return None

def auto_evaluation(golden_data, prediction_data):
    # Check if both files were successfully loaded and parsed
    if golden_data is not None and prediction_data is not None:
        # Extract the dictionaries from the "entities" field of each JSON file
        golden_entities = golden_data.get("entities", [])
        prediction_entities = prediction_data.get("entities", [])
        golden_entities_list = []
        for entities in golden_entities:
          golden_entities_list.extend(entities['texts'])
        prediction_entities_list = []
        for entities in prediction_entities:
          prediction_entities_list.extend(entities['texts'])

        golden_events = golden_data.get("events", [])
        prediction_events = prediction_data.get("events", [])

        # Find the best matching pairs between the dictionaries
        best_matches, id_map = find_best_matches_among_dicts(golden_entities, prediction_entities, "entity")

        # Mapping the entity ids in events by using id_map
        prediction_events = mapping_ids(prediction_events, id_map)

        prediction_group = group_dictionaries_by_type(prediction_events)
        golden_group = group_dictionaries_by_type(golden_events)

        # Check the number of each event type. There can be multiple dictionaries with the same event type.
        counts = counting_dict_for_each_type(golden_group, prediction_group)

        # Initialize counters for TP, FP, and FN
        entity_tp_count, entity_fp_count, entity_fn_count = 0, 0, 0
        event_tp_count, event_fp_count, event_fn_count = 0, 0, 0

        # Define the similarity threshold (e.g., 0.7 for 70%)
        similarity_threshold = 0.7

        for key, value in counts.items():
          if value['golden'] == 0:
            event_fp_count += value['prediction']
          elif value['prediction'] == 0:
            event_fn_count += value['golden']
          elif value['golden'] == 1 and value['prediction'] == 1:
            final_similarity = one_to_one_match_event(golden_group[key][0], prediction_group[key][0])
            print(final_similarity, str(key), str(golden_group[key][0]), str(prediction_group[key][0]))
            if final_similarity >= similarity_threshold:
              event_tp_count += 1
            else:
              event_fp_count += 1
              event_fn_count += 1
          else:
            best_event_matches, event_id_map = find_best_matches_among_dicts(golden_group[key], prediction_group[key], "event")
            for matches in best_event_matches:
              if matches[2] >= similarity_threshold:
                event_tp_count += 1
              else:
                event_fp_count += 1
                event_fn_count += 1

            event_fn_count += len(golden_group[key])
            event_fp_count += len(prediction_group[key])

        # Iterate through the best matching pairs and calculate similarity
        entity_pairs_list = []
        for golden_dict, prediction_dict, similarity in best_matches:
            # Calculate the similarity between "texts" values
            best_matching_entity_pairs = find_best_matches_in_list(golden_dict['texts'], prediction_dict['texts'])
            for pair in best_matching_entity_pairs:
              print(pair)
              if pair[2] > similarity_threshold:
                entity_tp_count += 1

        # get the total matching entities in one list
        flattened_entity_pairs = [item for sublist in entity_pairs_list for item in sublist]

        for pair in flattened_entity_pairs:
          print("pair: ", pair)

        # if prediction_entities_list contain more entities than the len of the flattened_entity_pairs,
        # that means there are FPs.
        if len(prediction_entities_list) > entity_tp_count:
          entity_fp_count += len(prediction_entities_list) - entity_tp_count

        # if golden_entities_list contains more entities than the len of the flattened_entity_pairs,
        # that means there are FNs.
        if len(golden_entities_list) > entity_tp_count:
          entity_fn_count += len(golden_entities_list) - entity_tp_count

        return entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count

def get_json_files(directory):
    json_files = [file for file in os.listdir(directory) if file.endswith('.json')]
    return json_files

def calculate_precision(tp, fp):
    if tp + fp == 0:
        return 0
    return tp / (tp + fp)

def calculate_recall(tp, fn):
    if tp + fn == 0:
        return 0
    return tp / (tp + fn)

def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)

def get_precision_recall_f1(entity_tp, entity_fp, entity_fn, event_tp, event_fp, event_fn):
  entity_precision = calculate_precision(entity_tp, entity_fp)
  entity_recall = calculate_recall(entity_tp, entity_fn)
  entity_f1 = calculate_f1(entity_precision, entity_recall)
  event_precision = calculate_precision(event_tp, event_fp)
  event_recall = calculate_recall(event_tp, event_fn)
  event_f1 = calculate_f1(event_precision, event_recall)
  return entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1

def total_evaluation(gold_path, prediction_path, output_path, gold_file_name, prediction_file_name):
  # sanity check - check if there are same number of gold files and prediction files
  gold_files = get_json_files(gold_path)
  prediction_files = get_json_files(prediction_path)
  assert len(gold_files) == len(prediction_files)

  total_list = []
  first_row = ['Gold', 'Prediction', 'Entity_TP', 'Entity_FP', 'Entity_FN', 'Event_TP', 'Event_FP', 'Event_FN', 'Entity_Precision', 'Entity_Recall', 'Entity_F1', 'Event_Precision', 'Event_Recall', 'Event_F1']
  total_list.append(first_row)
  n = 0
  while n < len(gold_files):
    print("processing "+str(n)+"th sentence!")
    golden_file = gold_path + "/"+ gold_file_name + str(n)+".json"
    prediction_file = prediction_path + "/"+ prediction_file_name +str(n) + ".json"
    golden_data = read_json_file(golden_file)
    prediction_data = read_json_file(prediction_file)
    if len(prediction_data['entities']) != 0:
      if 'texts' in prediction_data['entities'][0].keys():
        entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count = auto_evaluation(golden_data, prediction_data)
        entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1 = get_precision_recall_f1(entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count)
      else:
        print("**There's a format issue!**")
        entity_tp_count = 0
        entity_fp_count = len(prediction_data['entities'])
        entity_fn_count = len(golden_data['entities'])
        event_tp_count = 0
        event_fp_count = len(prediction_data['events'])
        event_fn_count = len(golden_data['events'])
        entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1 = get_precision_recall_f1(entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count)
      row = [golden_file, prediction_file, entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count, entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1]
      total_list.append(row)
    else:
      print("**No entity extracted!**")
      entity_tp_count = 0
      entity_fp_count = 0
      entity_fn_count = len(golden_data['events'])
      event_tp_count = 0
      event_fp_count = len(prediction_data['events'])
      event_fn_count = len(golden_data['events'])
      entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1 = get_precision_recall_f1(entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count)
      row = [golden_file, prediction_file, entity_tp_count, entity_fp_count, entity_fn_count, event_tp_count, event_fp_count, event_fn_count, entity_precision, entity_recall, entity_f1, event_precision, event_recall, event_f1]
      total_list.append(row)
    n += 1

  n = 0
  entity_tp_sum = 0
  entity_fp_sum = 0
  entity_fn_sum = 0
  event_tp_sum = 0
  event_fp_sum = 0
  event_fn_sum = 0
  while n < len(total_list):
    if n == 0:
      n += 1
    else:
      entity_tp_sum += total_list[n][2]
      entity_fp_sum += total_list[n][3]
      entity_fn_sum += total_list[n][4]
      event_tp_sum += total_list[n][5]
      event_fp_sum += total_list[n][6]
      event_fn_sum += total_list[n][7]
      n += 1
  entity_precision_sum, entity_recall_sum, entity_f1_sum, event_precision_sum, event_recall_sum, event_f1_sum = get_precision_recall_f1(entity_tp_sum, entity_fp_sum, entity_fn_sum, event_tp_sum, event_fp_sum, event_fn_sum)
  final_row = ["", "", entity_tp_sum, entity_fp_sum, entity_fn_sum, event_tp_sum, event_fp_sum, event_fn_sum, entity_precision_sum, entity_recall_sum, entity_f1_sum, event_precision_sum, event_recall_sum, event_f1_sum]
  total_list.append(final_row)

  output_file = output_path + "/" + "evaluation_result.csv"

  with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(total_list)

if __name__ == "__main__":
    main()