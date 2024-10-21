import os
import csv
import create_full_prompt
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def extract_information(prompt, target_text, model_name, client):
    response = client.chat.completions.create(
      model=model_name,
      response_format={
        'type': 'json_object',
      },
      messages=[
        {
          "role": "system",
          "content": prompt
        },
        {
          "role": "user",
          "content": target_text
        }
      ],
      temperature=0,
      max_tokens=4096,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def classification(prompt, target_text, client):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
              "role": "system",
              "content": prompt
            },
            {
              "role": "user",
              "content": target_text
            }
          ],
        temperature=0,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
    return response


def classify_text_list(text_list, client):
    with open("classification_prompt.txt", 'r') as file:
        prompt = file.read()
    total_classifications = []
    for text in text_list:
        classification_result = classification(prompt, text, client)
        total_classifications.append(eval(classification_result.choices[0].message.content))
    assert len(text_list) == len(total_classifications)
    return total_classifications


def main(text_list):
    # prompt the user to choose model
    model_name = input("Please choose the model (gpt-4-1106-preview or gpt-4o-mini-2024-07-18): ")

    # ask the user for the directory and num_of_examples (used for prompt creation)
    directory = input("Please provide the path to the prompt examples: ")
    num_of_examples = input("How many examples do you want to use for each event type? ")

    if model_name in ['gpt-4-1106-preview', 'gpt-4o-mini-2024-07-18']:
        # prompt the user for their api key
        key = input("Please enter your openai api key: ")
        client = OpenAI(api_key=key)

        # make predictions using pretrained models
        preds = classify_text_list(text_list, client)

        # check if the length of preds and text_list are equal
        assert len(preds) == len(text_list)

        # using predictions, create prompts and extract information
        extracted_info = []
        n = 0
        while n < len(text_list):
            print("processing " + str(n+1) + "th sentence!")
            # try:
            full_prompt = create_full_prompt.main(directory, preds[n], num_of_examples)
            response = extract_information(full_prompt, text_list[n], model_name, client)
            extracted_info.append(response.choices[0].message.content)
            n += 1
            # except:
            #     print("something went wrong while processing " + str(n) + "th text!")
        return extracted_info
    else:
        print("Please choose between gpt-4-1106-preview and gpt-4o-mini-2024-07-18!")
