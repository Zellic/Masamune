import requests
import json

"""
Retrieve the latest BugFixesReviews from the Immunefi Github.

The resource is located at:

https://raw.githubusercontent.com/immunefi-team/Web3-Security-Library/main/BugFixReviews/README.md

The resource is updated every once in a while.
"""


def get_filter_bugfixreviews():
    """
    Retrieve the latest BugFixesReviews from the Immunefi Github, and filter them to return only the relevant information.
    """

    # Query the resource
    response = requests.get("https://raw.githubusercontent.com/immunefi-team/Web3-Security-Library/main/BugFixReviews/README.md")

    # Parse the response, adding each line to a list
    lines = response.text.splitlines()

    # Filter the list, keeping only the lines that start with "### [" which point to the Hacks, and the immediate next line, and the one that start with " - Vulnerability Type: " which point to the type of the hack
    filtered_lines = {line[3:]: [lines[i+2], lines[i+4] if lines[i+4].startswith("-") or lines[i+4].startswith("Vulnerability") else lines[i+3]] for i, line in enumerate(lines) if line.startswith("### [") or line.startswith(" ### [")}

    resulting_array = []

    for key, value in filtered_lines.items():

        hack_name = key.split("]")[0][1:].strip(" [")
        hack_link = key.split("(")[1][:-1]

        hack_description = value[0].strip(" #")
        if hack_description == "":
            hack_description = "Unknown, check manually"

        try:
            hack_type = value[1].strip(" -").split(":")[1].strip(" ")
        except IndexError:
            hack_type = "Unknown, check manually"
        
        if hack_type == "":
            hack_type = "Unknown, check manually"

        # hack_type may be a list, so we need to split it by comma
        hack_type = hack_type.split(",")

        resulting_array.append({
            "title": hack_name,
            "html_url": hack_link, 
            "description": hack_description, 
            "labels": hack_type
        })

    return resulting_array

def save_result(results_array):
    """
    Save the results to a json file.
    """
    
    # Update the `immunefi_findings.json` file
    with open("../results/immunefi_findings.json", "w") as f:
        json.dump(
            results_array,
            f
        )

if __name__ == "__main__":
    resulting_array = get_filter_bugfixreviews()
    save_result(resulting_array)
