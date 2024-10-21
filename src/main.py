import argparse
import classification, full_examples, ceiling
import json
import csv


def open_csv(input_path):
    text_list = []
    pred_list = []
    with open(input_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader, None)
        for row in csvreader:
            text_list.append(row[0])
            preds = [eval(i) for i in row[1:]]
            pred_list.append(preds)
    return text_list, pred_list


def export_to_json(extracted_info, output_path, output_file_name):
    n = 0
    for response in extracted_info:
        try:
            extracted_json = json.loads(response)
            with open(output_path + "/" + output_file_name + "_" + str(n)+'.json', 'w') as f:
                json.dump(extracted_json, f, indent=4)
            n += 1
        except:
            print("data number " + str(n) + " was not saved as json")
            n += 1


def main():
    # get the path to the input file as an argument
    parser = argparse.ArgumentParser(description='Provide input file, output path, output file names and text extraction model')
    parser.add_argument('input_file', type=str, help='Path to the input file (in csv format)')
    parser.add_argument('output_path', type=str, help='Path to the output files')
    parser.add_argument('output_file_name', type=str, help='Output file name')
    parser.add_argument('te_model', type=str, help='Select text extraction model: classification, full_examples, ceiling', default='classification')
    args = parser.parse_args()
    file_path = args.input_file
    te_model = args.te_model
    output_path = args.output_path
    output_file_name = args.output_file_name
    texts, preds = open_csv(file_path)

    if te_model == "classification":
        extracted_info = classification.main(texts)
        export_to_json(extracted_info, output_path, output_file_name)

    elif te_model == "full_examples":
        extracted_info = full_examples.main(texts)
        export_to_json(extracted_info, output_path, output_file_name)
    
    elif te_model == "ceiling":
        extracted_info = ceiling.main(texts, preds)
        export_to_json(extracted_info, output_path, output_file_name)

    else:
        print("please choose text extraction model between 'classification', 'full_examples', and 'ceiling'!")


if __name__ == "__main__":
    main()
