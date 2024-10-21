# This code is for evaluation purpose only
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


def main(texts, preds):
    # prompt the user to choose model
    model_name = input("Please choose the model (gpt-4-1106-preview or gpt-4o-mini-2024-07-18): ")

    # ask the user for the directory and num_of_examples (used for prompt creation)
    directory = input("Please provide the path to the prompt examples: ")
    num_of_examples = input("How many examples do you want to use for each event type? ")

    # check if the length of texts and preds are equal
    assert len(texts) == len(preds)

    if model_name in ['gpt-4-1106-preview', 'gpt-4o-mini-2024-07-18']:
        # prompt the user for their api key
        key = input("Please enter your openai api key: ")
        client = OpenAI(api_key=key)
        # using predictions, create prompts and extract information
        extracted_info = []
        n = 0
        while n < len(texts):
            print("processing " + str(n+1) + "th sentence!")
            try:
                full_prompt = create_full_prompt.main(directory, preds[n], num_of_examples)
                response = extract_information(full_prompt, texts[n], model_name, client)
                extracted_info.append(response.choices[0].message.content)
                n += 1
            except:
                print("something went wrong while processing " + str(n) + "th text!")
                return extracted_info
        return extracted_info
    else:
        print("Please choose between gpt-4-1106-preview or gpt-4o-mini-2024-07-18!")
