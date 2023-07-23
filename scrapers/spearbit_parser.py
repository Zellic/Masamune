# Parse Trail Of Bits generic format pdf audits via the pdfminer.six library
from pdfminer.high_level import extract_text
import re
import os
import json


def extract_finding(pdf_name):
    text = extract_text("../pdfs/spearbit-reports/pdfs/" + pdf_name)

    # Exclude ToC
    text_after_findings = text[text.find("Findings") + len("Findings"):]

    after_toc = text_after_findings[text_after_findings.find("Findings"):text_after_findings.find("Appendix")]
    
    # Handle LiquidCollective report differently to avoid including section 7 appendix items among findings
    if pdf_name == "LiquidCollective-Spearbit-Security-Review.pdf":
        text_after_findings = text[text.find("Test Cases") + len("Test Cases"):]
        after_toc = text_after_findings[text_after_findings.find("Findings"):text_after_findings.find("Test Cases")]

    # Handle CronFinance because Appendix keyword occurs before it should
    if pdf_name == "CronFinance-Spearbit-Security-Review.pdf":
        second_appendix_index = text_after_findings[text_after_findings.find("Appendix") + 10:].find("Appendix")
        after_toc = text_after_findings[text_after_findings.find("Findings"):second_appendix_index]

    # if after_toc is zero, don't look for the appendix
    if len(after_toc) == 0:
        after_toc = text_after_findings[text_after_findings.find("Findings"):]

    # overwrite text with cached report after ToC
    text = after_toc

    # Only keep lines that start with "number.number.number " or " number.number.number "
    after_toc = "\n".join([x for x in after_toc.splitlines() if re.match(r'\d+\.\d+\.\d+\s+', x) or re.match(r'\s+\d+\.\s+\d+\.\s+\d+\s+', x)])

    # print(after_toc)
    for elem in after_toc.splitlines():
        if elem[0] == " ":
            after_toc = after_toc.replace(elem, elem[1:])    

    # try:
    #     text = text.split("Description:")[1]
    # except IndexError:
    #     with open("spearbit_parser_errors.txt", "a") as f:
    #         f.write(pdf_name + "\n")
    #         return

    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)

    # Take each line and make it one element of a list
    after_toc = after_toc.splitlines()

    finding_titles = [x for x in after_toc if x != '']

    # print(finding_titles)

    ordered_findings = [] 
    for index, finding in enumerate(finding_titles):
        try:
            ordered_findings.append(text[text.find(finding):text.find(finding_titles[index + 1])])
        except IndexError: # enter here if this is the last finding in the report
            ordered_findings.append(text[text.find(finding):])

    if len(ordered_findings) == 0:
        with open("errors.txt", "a") as f:
            f.write(pdf_name + "\n")
            return

    # Save the findings to a file
    with open(f"../findings_newupdate/spearbit/{pdf_name[:-4]}.txt", "w") as f:
        for elem in ordered_findings:
            if elem == "":
                continue
            f.write(elem + "\n")

def jsonify_findings(pdf_name):

    try:
        with open(f"../findings_newupdate/spearbit/{pdf_name[:-4]}.txt", "r") as f:
            findings = f.read().splitlines()
    except FileNotFoundError:
        return

    result = []

    for finding in findings:

        """
        The format of a finding looks like this:
        5.2.5 settleAuction() doesn't check if the auction was successful Severity: High Risk Context: CollateralToken.sol#L600 Description: settleAuction() is a privileged functionality called by LienToken.payDebtViaClearingHouse(). settleAuction() is intended to be called on a successful auction, but it doesn't verify that that's indeed the case. Anyone can create a fake Seaport order with one of its considerations set as the CollateralToken as described in Issue 93. Another potential issue is if the Seaport orders can be "Restricted" in future, then there is a possibility for an authorized entity to force settleAuction on CollateralToken, and when SeaPort tries to call back on the zone to validate it would fail. Recommendation: The following validations can be performed: • CollateralToken doesn't own the underlying NFT. • collateralIdToAuction[collateralId] is active. Now, settleAuction() can only be called on the success of the Seaport auction created by Astaria protocol. 18

        We want to extract the following:
        "title": "settleAuction() doesn't check if the auction was successful",
        "html_url": "https://github.com/spearbit/portfolio/tree/master/pdfs/Astaria-Spearbit-Security-Review.pdf",
        "body": "settleAuction() is a privileged functionality called by LienToken.payDebtViaClearingHouse(). settleAuction() is intended to be called on a successful auction, but it doesn't verify that that's indeed the case. Anyone can create a fake Seaport order with one of its considerations set as the CollateralToken as described in Issue 93. Another potential issue is if the Seaport orders can be \"Restricted\" in future, then there is a possibility for an authorized entity to force settleAuction on CollateralToken, and when SeaPort tries to call back on the zone to validate it would fail.",
        "labels": [
            "Spearbit",
            "Astaria",
            "Severity: High Risk"
        ]

        """

        # finding = finding.encode("ascii", "ignore").decode()

        # Get the title
        numbered_title = finding.split("Severity:")[0].strip()
        title = numbered_title[numbered_title.find(" "):].strip()

        # Get the Severity
        # Sometimes Context is skipped, so check if Context exists
        if finding.find("Context:") > 0:
            if finding.find("Severity:") < 0: # Seaport report has this special case
                numbered_title = finding.split("Context:")[0].strip()
                title = numbered_title[numbered_title.find(" "):].strip()
                context = finding.split("Context:")[1].split("Description:")[0].strip()
            else:
                severity = finding.split("Severity:")[1].split("Context:")[0].strip()
                context = finding.split("Context:")[1].split("Description:")[0].strip()
        elif finding.find("Context") > 0: # Sometimes the : is missing
            severity = finding.split("Severity:")[1].split("Context")[0].strip()
            context = finding.split("Context")[1].split("Description:")[0].strip()
        else: # This case only happens in a few places
            if finding.find("Description") < 0: # Sometimes the : is missing
                try:
                    severity = finding.split("Severity:")[1].split(" ")[:3] # using index of 3 will only cause problems for informational
                except IndexError:
                    continue
            else:
                severity = finding.split("Severity:")[1].split("Description:")[0].strip()

        try:
        # Get the description and recommendation separately
        # Sometimes they are combined
            if finding.find("Description / Recommendation:") >= 0:
                description = finding.split("Description / Recommendation:")[1].strip()
                recommendation = description
            else:
                description = finding.split("Description:")[1].split("Recommendation:")[0].strip()
                recommendation = finding.split("Recommendation:")[1].strip()
        except IndexError:
            continue

        protocol = ""
        try:
            # Get the protocol name
            protocol = pdf_name[:pdf_name.find("-Spearbit-")]
        except IndexError:
            continue
        
        # If protocol name could not be parsed, use PDF name
        if not protocol:
            protocol = pdf_name[:-4]

        result.append(
            {
                "title": title.encode("ascii", "ignore").decode(),
                "html_url": "https://github.com/spearbit/portfolio/tree/master/pdfs/" + pdf_name,
                # clean utf-8 characters
                "body": description.encode("ascii", "ignore").decode(),
                "labels": [
                    "Spearbit",
                    protocol.encode("ascii", "ignore").decode(),
                    "Severity: " + severity.encode("ascii", "ignore").decode()
                ]
            }
        )

    # load the existing json file and append the new findings
    try:
        with open("../results/spearbit_findings.json", "r") as f:
            existing_findings = json.load(f)
    except FileNotFoundError:
        existing_findings = []

    with open("../results/spearbit_findings.json", "w") as f:
        json.dump(existing_findings + result, f, indent=4)
        
        
if __name__ == "__main__":

    # Step 1: Extract findings text from PDFs
    for pdf_file in os.listdir("../pdfs/spearbit-reports/pdfs"):
        extract_finding(pdf_file)

    # Step 2: Parse findings text into JSON
    for json_file in os.listdir("../pdfs/spearbit-reports/pdfs"):
        jsonify_findings(json_file)

    # Step 3: deduplicate findings
    # only keep unique findings, the file contains an array of findings
    with open("../results/spearbit_findings.json", "r") as f:
        findings = json.load(f)

    unique_findings = []
    for finding in findings:
        if finding not in unique_findings:
            unique_findings.append(finding)

    # Step 4: write only unique findings to final json
    with open("../results/spearbit_findings.json", "w") as f:
        json.dump(unique_findings, f, indent=4)

    