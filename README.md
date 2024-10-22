# Prompt Chaining Technique for Information Extraction

This repository contains the corpus and code for the paper "Classify First, and Then Extract: Prompt Chaining Technique for Information Extraction" (To appear in the proceeding of the Natural Legal Language Processing Workshop 2024 (co-located at EMNLP 2024)).

## About The Project

This project introduces a new task-aware prompt design and example retrieval approach for information extraction (IE) using a prompt chaining technique. Our approach divides IE tasks into two steps: (1) text classification to understand
what information (e.g., entity or event types) is contained in the underlying text and (2) information extraction for the identified types. Initially, we use a large language model (LLM) in a few-shot setting to classify the contained information. The classification output is used to select the relevant prompt and retrieve the examples relevant to the input text. With the generated prompt, we ask a LLM to do the information extraction.

We evaluated GPT-4 and GPT-4o-mini on a legal IE task, demonstrating that prompt chaining enhances the model’s performance in a few-shot setting compared to the baseline, where examples from all possible classes are included in a single prompt. This approach is particularly useful in low-resource scenarios, as it does not require extensive training data. Additionally, it can be easily adapted to various IE tasks by adjusting the prompts. Finally, it offers a cost benefit by reducing the number of tokens used in the prompt.

For more details, please see our paper [here](https://clulab.org/papers/nllp2024_kwak-et-al.pdf).

## Usage

### Datasets

We used a legal will dataset introduced by [Kwak et al. (2023)](https://aclanthology.org/2023.findings-emnlp.287.pdf), which can be accessed [here](https://github.com/ml4ai/ie4wills). To adapt the dataset for this project, we used `annotation_format_translator.py` to convert its format. For a more detailed guide on how to use the code, please refer to the section below.

The dataset in the converted format is located in the `/data` directory. The system's input files are in `.csv` format, and the gold data for evaluation can be found in directories with `_gold` in their names. Examples for text classification prompt are provided in the `example_pool` folder.

### Codes

#### Annotation format translator

This program is for converting the format of the legal will dataset introduced by [Kwak et al. (2023)](https://aclanthology.org/2023.findings-emnlp.287.pdf), which can be accessed [here](https://github.com/ml4ai/ie4wills). To run this program, use the following command:
`
python format_translator.py "path/to/the/dataset.json" "path/to/your/outputs"
`

#### Information extraction system

1. Requirements

To run the information extraction system, you will need an OpenAI API key.

2. Running the program

To run the system, use the following command:

```
python main.py "path/to/the/input/file" "path/to/the/output/files" "output_file_name" "text_extraction_model"
```

- Input: The input file should be in .csv format. You can use `test.csv` and `ood.csv` to replicate our study.
- Output: All output files will be named using the specified "output_file_name," with an index appended to the end.
- Text Extraction Model: You can choose from three models: "classification", "ceiling", or "full_example". For a detailed explanation of each model, refer to our [paper](https://clulab.org/papers/nllp2024_kwak-et-al.pdf).

If you run the code, you will be prompted to:
- select an LLM for information extraction: Choose between `gpt-4-1106-preview` and `gpt-4o-mini-2024-07-18`. 
- provide a path to the example pool: To replicate our study, you can the use the `example_pool` directory. 
- set the number of examples for *k*-shot prompting: Define the number of examples (*k*-value) to include in the information extraction prompt. We recommend starting with 5 and adjusting as needed.
- enter your OpenAI API key: This is required to access the LLMs.

#### Auto evaluator

This program is for evaluating the LLM's outputs automatically by comparing them with gold data. The evaluator uses a default similarity threshold of 0.7, which can be adjusted at line 236 of the code (`auto_evaluator.py`). To make the evaluation more stringent, increase the threshold; for a more flexible evaluation, decrease it. 

1. Requirements

Before using the auto evaluator, please ensure the following:

(1) Data Matching: There must be an equal number of gold data files and prediction (pred) data files. 

(2) File Naming Rules: All files should follow a consistent naming convention, differing only by an index (e.g., `test_human_annotations_` for the gold data and `test_five_shots_classification_` for the predictions generated from a five-shot classification model). Gold and prediction files should be paired by matching the index at the end of their filenames (e.g., `test_human_annotations_0.json` and `test_five_shots_classification_0.json`).

2. Running the program

To run the program, use the following command:
```
python auto_evaluator.py "path/to/your/gold_files" "path/to/your/pred_files" "path/to/your/output" "gold_file_name" "pred_file_name"
```

In the `"gold_file_name"` and `"pred_file_name"` arguments, provide the common prefix of the data files (e.g., `"test_human_annotations_"` and `"test_five_shots_classification_"`).

## License

This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License. See [LICENSE.md](https://github.com/ml4ai/pc4wills/blob/main/LICENSE.md) for more details.

## Paper

If you use this data or code, please cite our paper:

```
@inproceedings{kwak-et-al-nllp2024-error-analysis,
    title = "Classify First, and Then Extract: Prompt Chaining Technique for Information Extraction",
    author = "Alice Kwak and Clayton Morrison and Derek Bambauer and Mihai Surdeanu",
    booktitle = "Proceedings of the Natural Legal Language Processing Workshop 2024",
    month = nov,
    year = "2024",
    url = "https://clulab.org/papers/nllp2024_kwak-et-al.pdf",
    abstract = "This work presents a new task-aware prompt design and example retrieval approach for information extraction (IE) using a prompt chaining technique. Our approach divides IE tasks into two steps: (1) text classification to understand what information (e.g., entity or event types) is contained in the underlying text and (2) information extraction for the identified types. Initially, we use a large language model (LLM) in a few-shot setting to classify the contained information. The classification output is used to select the relevant prompt and retrieve the examples relevant to the input text. Finally, we ask a LLM to do the information extraction with the generated prompt. By evaluating our approach on legal IE tasks with two different LLMs, we demonstrate that the prompt chaining technique improves the LLM’s overall performance in a few-shot setting when compared to the baseline in which examples from all possible classes are included in the prompt. Our approach can be used in a low-resource setting as it does not require a large amount of training data. Also, it can be easily adapted to many different IE tasks by simply adjusting the prompts. Lastly, it provides a cost benefit by reducing the number of tokens in the prompt.",
}
```

## Contact

If you have any questions or comments on our work, please contact the person below.

Alice Kwak - alicekwak@arizona.edu