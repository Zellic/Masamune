# Parse yAudit markdown reports
import os
import json
import re
import marko
from bs4 import BeautifulSoup

### Update Process
# 1. Copy all markdown files from the "reports" directory in this repo https://github.com/yAudit/reports-website/tree/main/reports
# into the pdf/yaudit-reports/ directory
# 2. (Optional) for extra assurance, delete the results/yaudit_findings.json file and the findings_newupdate/yaudit directory
# 3. Make sure no calls in the `main` function are commented out, then run this script

def extract_finding(md_name):
    file_location = "../pdfs/yaudit-reports/" + md_name
    with open(file_location, 'r') as markdown_text:
        # Retrieve text from markdown file
        markdown_data = markdown_text.read()
    
    # render markdown file to html for easier parsing
    rendered_html = marko.convert(markdown_data)
    # Remove the leading <hr> to simplify later steps
    html_without_leading_hr = rendered_html[7:]
    # Find the portion of the report with all the findings information
    first_selection = html_without_leading_hr[html_without_leading_hr.find("<hr />"):html_without_leading_hr.find("Final Remarks")]
    # Parse selected HTML data with beautiful soup
    soup = BeautifulSoup(first_selection, "html.parser")

    # Loop through all findings
    counter = 0
    findings = ""
    finding_description = ""
    # Findings all use header h3
    finding_titles = soup.find_all("h3")
    for finding in finding_titles:
        # Remove HTML flags
        unhtmlified_finding = BeautifulSoup(str(finding), "lxml").text
        # Need to do a regex match to remove lines that are not actual findings
        if re.match(r'\d+\.\s+\w+', unhtmlified_finding):
            counter += 1

            # At this point, we identified the finding title. Now to clean it up
            finding_title = unhtmlified_finding[unhtmlified_finding.find(" - ") + len(" - "):]
            if finding_title.find(" (") > 1:
                finding_title = finding_title[:finding_title.find(" (")]

            # Extract finding severity
            finding_severity = unhtmlified_finding[unhtmlified_finding.find(". ") + len(". "):unhtmlified_finding.find(" - ")].strip()
            severities = ["Critical", "High", "Medium", "Low", "Gas", "Informational"]
            if finding_severity not in severities:
                finding_severity = "Unknown"

            # Extract finding description
            finding_details = rendered_html[rendered_html.find(str(finding)):]
            # Older reports used PoC header, newer ones use Technical Details, and some are mixed
            poc_location = finding_details.find("<h4>Proof of concept</h4>")
            techdetails_location = finding_details.find("<h4>Technical Details</h4>")
            impact_location = finding_details.find("<h4>Impact</h4>")
            if impact_location > 0 and (impact_location < poc_location or impact_location < techdetails_location):
                finding_description = ""
            elif poc_location > 0 and (poc_location < techdetails_location or techdetails_location < 0):
                finding_description = finding_details[poc_location + len("<h4>Proof of concept</h4>"):finding_details.find("<h4>Impact</h4>")]
                finding_description = re.sub(r'\s+', ' ', BeautifulSoup(str(finding_description), "lxml").text)
            elif techdetails_location > 0 and (poc_location < 0 or techdetails_location < poc_location):
                finding_description = finding_details[techdetails_location + len("<h4>Technical Details</h4>"):finding_details.find("<h4>Impact</h4>")]
                finding_description = re.sub(r'\s+', ' ', BeautifulSoup(str(finding_description), "lxml").text)

            # Concatenate everything together to save in text file
            findings += str(counter) + ". " + finding_title + " Severity: " + finding_severity + " Difficulty: n/a Type: n/a Target: n/a Description: " + BeautifulSoup(str(finding_description), "lxml").text + "\n"

    with open(f"../findings_newupdate/yaudit/{md_name[:-3]}.txt", "w") as f:
        f.write(findings)

def jsonify_findings(md_name):
    result = []

    try:
        with open(f"../findings_newupdate/yaudit/{md_name[:-3]}.txt", "r") as f:
            findings = f.read().splitlines()
    except FileNotFoundError:
        print("ERROR in opening file")
        return

    for finding in findings:

        """
        The format of a finding looks like this:
        2. MobileCoin Foundation could infer token IDs in certain scenarios Severity: Informational Difficulty: High Type: Data Exposure Finding ID: TOB-MCCT-2 Target: Various

        We want to extract the following:
        "title": "MobileCoin Foundation could infer token IDs in certain scenarios",
        "labels": [
            "yAudit",
            "Severity: Informational",
            "Difficulty: High",
            "Type: Data Exposure",
        ]
        "description": ...

        """

        # finding = finding.encode("ascii", "ignore").decode()

        # Get the title
        title = finding.split("Severity:")[0].strip()

        try:
        # Get the Severity
            severity = finding.split("Severity:")[1].split("Difficulty:")[0].strip()
        except IndexError:
            continue

        # Get the Difficulty
        difficulty = finding.split("Difficulty:")[1].split("Type:")[0].strip()

        # Get the description, which is all the text after the first encounter of "Description"

        description = finding.split("Description:")[1].strip()

        # description.encode("ascii", "ignore").decode()
    
        result.append(
            {
                "title": title.encode("ascii", "ignore").decode(),
                "html_url": "https://github.com/yAudit/reports/blob/main/md/" + md_name,
                # clean utf-8 characters
                "body": description.encode("ascii", "ignore").decode(),
                "labels": [
                    "yAudit",
                    "Severity: " + severity.encode("ascii", "ignore").decode(),
                    "Difficulty: " + difficulty.encode("ascii", "ignore").decode(),
                ]
            }
        )

    # load the existing json file and append the new findings
    try:
        with open("../results/yaudit_findings.json", "r") as f:
            existing_findings = json.load(f)
    except FileNotFoundError:
        existing_findings = []

    with open("../results/yaudit_findings.json", "w") as f:
        json.dump(existing_findings + result, f, indent=4)

if __name__ == "__main__":

    for md_file in os.listdir("../pdfs/yaudit-reports/"):
         extract_finding(md_file)

    for md_file in os.listdir("../pdfs/yaudit-reports/"):
         jsonify_findings(md_file)