# Parse Trail Of Bits generic format pdf audits via the pdfminer.six library
from pdfminer.high_level import extract_text
import re
import os
import json


def extract_finding(pdf_name):

    try:
        text = extract_text("../pdfs/publications/reviews/" + pdf_name)
    except:
        with open("errors.txt", "a") as f:
            f.write(pdf_name + "\n")
            return

    first_selection = text[text.find("Detailed Findings"):text.find("Summary of Recommendations")]

    # Only keep lines that start with "number. [some text]" or " number. [some text]"
    first_selection = "\n".join([x for x in first_selection.splitlines() if re.match(r'\d+\.\s+\w+', x) or re.match(r'\s+\d+\.\s+\w+', x)])
    
    # print(first_selection[0])
    for elem in first_selection.splitlines():
        if elem[0] == " ":
            first_selection = first_selection.replace(elem, elem[1:])    

    try:
        text = text.split("Detailed Findings")[2]
    except IndexError:
        with open("errors.txt", "a") as f:
            f.write(pdf_name + "\n")
            return

    # get all the text until "Summary of Recommendations"

    text = text.split("Summary of Recommendations")[0]

    # remove every occurence of the word "PUBLIC", "Trail of Bits", and "Shell Protocol v2 Security Assessment"

    text = text.replace("PUBLIC", "")
    text = text.replace("Trail of Bits", "")

    # Remove anything of the form "18 Shell Protocol v2 Security Assessment
    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r"\b\d+\s+\w+(?:\s+\w+)*\s+Security Assessment\b", '', text)

    # Remplace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)

    # Remove "Detailed Findings" from the list
    first_selection = first_selection.replace("Detailed Findings", "")

    # Take each line and make it one element of a list
    first_selection = first_selection.splitlines()

    finding_titles = [x for x in first_selection if x != '']

    # print(finding_titles)

    ordered_findings = [] 
    for index, finding in enumerate(finding_titles):
        try:
            ordered_findings.append(text[text.find(finding):text.find(finding_titles[index + 1])])
        except IndexError:
            ordered_findings.append(text[text.find(finding):])

    if len(ordered_findings) == 0:
        with open("errors.txt", "a") as f:
            f.write(pdf_name + "\n")
            return

    # Save the findings to a file
    with open(f"../findings_newupdate/tob/{pdf_name[:-4]}.txt", "w") as f:
        for elem in ordered_findings:
            if elem == "":
                continue
            f.write(elem + "\n")

def jsonify_findings(pdf_name):

    try:
        with open(f"../findings_newupdate/tob/{pdf_name[:-4]}.txt", "r") as f:
            findings = f.read().splitlines()
    except FileNotFoundError:
        return

    result = []

    for finding in findings:

        """
        The format of a finding looks like this:
        2. MobileCoin Foundation could infer token IDs in certain scenarios Severity: Informational Diﬃculty: High Type: Data Exposure Finding ID: TOB-MCCT-2 Target: Various

        We want to extract the following:
        "title": "MobileCoin Foundation could infer token IDs in certain scenarios",
        "labels": [
            "Trail of Bits",
            "Severity: Informational",
            "Diﬃculty: High",
            "Type: Data Exposure",
        ]
        "body": ...

        """

        # finding = finding.encode("ascii", "ignore").decode()

        # Get the title
        title = finding.split("Severity:")[0]
        
        try:
        # Get the Severity
        # Sometimes Difficulty is after Severity, sometimes Type is after Severity
            severity_difficulty = finding.split("Severity:")[1].split("Diﬃculty:")[0].strip()
            severity_type = finding.split("Severity:")[1].split("Type:")[0].strip()
            if len(severity_difficulty) < len(severity_type):
                severity = severity_difficulty
            else:
                severity = severity_type
        except IndexError:
            continue

        # Get the Difficulty
        # Sometimes Type is after Difficulty, sometimes Finding ID is after Difficulty
        difficulty_type = finding.split("Diﬃculty:")[1].split("Type:")[0].strip()
        difficulty_findingid = finding.split("Diﬃculty:")[1].split("Finding ID:")[0].strip()
        if len(difficulty_type) < len(difficulty_findingid):
            difficulty = difficulty_type
        else:
            difficulty = difficulty_findingid

        # Get the description, which is all the text after the first encounter of "Description"

        description = finding.split("Description")[1].strip()

        # description.encode("ascii", "ignore").decode()
    
        result.append(
            {
                "title": title.encode("ascii", "ignore").decode(),
                "html_url": "https://github.com/trailofbits/publications/tree/master/reviews/" + pdf_name,
                # clean utf-8 characters
                "body": description.encode("ascii", "ignore").decode(),
                "labels": [
                    "Trail of Bits",
                    "Severity: " + severity.encode("ascii", "ignore").decode(),
                    "Difficulty: " + difficulty.encode("ascii", "ignore").decode(),
                ]
            }
        )

    # load the existing json file and append the new findings
    try:
        with open("../results/tob_findings.json", "r") as f:
            existing_findings = json.load(f)
    except FileNotFoundError:
        existing_findings = []

    with open("../results/tob_findings.json", "w") as f:
        json.dump(existing_findings + result, f, indent=4)
        
        
if __name__ == "__main__":

    for pdf_file in os.listdir("../pdfs/publications/reviews"):
        try:
            extract_finding(pdf_file)
        except:
            print("SOME ISSUE WITH " + pdf_file)

    for json_file in os.listdir("../pdfs/publications/reviews"):
        jsonify_findings(json_file)

    # only keep unique findings, the file contains an array of findings
    with open("../results/tob_findings.json", "r") as f:
        findings = json.load(f)

    unique_findings = []
    for finding in findings:
        if finding not in unique_findings:
            unique_findings.append(finding)

    with open("../results/tob_findings.json", "w") as f:
        json.dump(unique_findings, f, indent=4)

    