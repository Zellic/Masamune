# Parse Trail Of Bits generic format pdf audits via the pdfminer.six library
from pdfminer.high_level import extract_text
import re
import os
import json


def extract_finding(pdf_path):
    text = extract_text("../pdfs/dedaub-audits/" + pdf_path)
    text_file_name = pdf_path[:-4]
    text_file_name = text_file_name.replace("/", " _ ") + ".txt"

    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove null characters, unfortunately the pdf doesn't parse everything and this will leave typos
    text = re.sub(r'\00', '', text)

    # Remove artifacts from pdf parsing
    dedaub_len = len("DEDAUB.COM")
    indices = [m.start() for m in re.finditer("DEDAUB.COM", text)]
    indices.reverse() # use reverse order so that removing text does not impact the other indices
    if indices:
        for word_index in indices:
            # subtract 2 from index because we want to remove the page number too
            text = text[:word_index-2] + text[word_index+dedaub_len:]

    # Ignore the preamble, skip to the findings
    # Some reports use &, other times "and"
    if text.lower().find("vulnerabilities and functional issues") > 0:
        text_findings = text[text.lower().find("vulnerabilities and functional issues"):text.lower().find("disclaimer")]
    elif text.lower().find("vulnerabilities & functional issues") > 0:
        text_findings = text[text.lower().find("vulnerabilities & functional issues"):text.lower().find("disclaimer")]
    else:
        print("Error parsing " + pdf_path)
        return

    # overwrite text with cached report after ToC
    text = text_findings

    # Only keep lines that start with "ID Description" or similar text, insert newline to enable splitlines later
    text_findings = text_findings.replace(' ID Description', ' ID Description\n')
    text_findings = text_findings.replace(' Id Description', ' ID Description\n')
    text_findings = text_findings.replace(' Nr. Description', ' ID Description\n')

    finding_titles = []
    for section in text_findings.splitlines():
        section = section.strip()
        pattern = re.compile('[A-Z]\d+\s') # finding identifier is a combination of a letter and a number
        finding_identifiers = pattern.findall(section)
        for counter in range(len(finding_identifiers) - 1):
            if counter < len(finding_identifiers):
                finding_titles.append(section[section.find(finding_identifiers[counter]):section.find(finding_identifiers[counter+1])])
            else:
                finding_titles.append(section[section.find(finding_identifiers[counter]):])

    # text_findings = "\n".join([x for x in text_findings.splitlines() if re.match(r' ID Descrip\S+', x) or re.match(r' Id Descrip\S+', x) or re.match(r' Nr. Descrip\S+', x)])

    # try:
    #     text = text.split("Description:")[1]
    # except IndexError:
    #     with open("dedaub_parser_errors.txt", "a") as f:
    #         f.write(pdf_path + "\n")
    #         return

    finding_titles = [x for x in finding_titles if x != '']

    # print(finding_titles)

    ordered_findings = [] 
    for index, finding in enumerate(finding_titles):
        try:
            find = text[text.find(finding):text.find(finding_titles[index + 1])]
            ordered_findings.append(find.encode("ascii", "ignore").decode())
        except IndexError: # enter here if this is the last finding in the report
            find = text[text.find(finding):]
            ordered_findings.append(find.encode("ascii", "ignore").decode())

    if len(ordered_findings) == 0:
        with open("errors.txt", "a") as f:
            f.write(pdf_path + "\n")
            return

    # Save the findings to a file
    with open(f"../findings_newupdate/dedaub/{text_file_name}", "w") as f:
        for elem in ordered_findings:
            if elem == "":
                continue
            f.write(elem + "\n")

def jsonify_findings(json_name):

    try:
        with open(f"../findings_newupdate/dedaub/{json_name}", "r") as f:
            findings = f.read().splitlines()
    except FileNotFoundError:
        return

    result = []

    for finding in findings:

        """
        The format of a finding looks like this:
        5.1.1 LienToken.transferFrom does not update a public vault's bookkeeping parameters when a lien is transferred to it. Severity: Critical Risk Context: LienToken.sol#L303 Description: When transferFrom is called, there is not check whether the from or to parameters could be a public vault. Currently, there is no mechanism for public vaults to transfer their liens. But private vault owners who are also owners of the vault's lien tokens, they can call transferFrom and transfer their liens to a public vault. In this case, we would need to make sure to update the bookkeeping for the public vault that the lien was transferred to. On the LienToken side, s.LienMeta[id].payee needs to be set to the address of the public vault. And on the PublicVault side, yIntercept, slope, last, epochData of VaultData need to be updated (this requires knowing the lien's end). However, private vaults do not keep a record of these values, and the corresponding values are only saved in stacks off-chain and validated on-chain using their hash. Recommendation: • Either to block transferring liens to public vaults or • Private vaults or the LienToken would need to have more storage parameters that would keep a record of some values for each lien so that when the time comes to transfer a lien to a public vault, the parameters mentioned in the Description can be updated for the public vault.

        We want to extract the following:
        "title": "MobileCoin Foundation could infer token IDs in certain scenarios",
        "labels": [
            "Trail of Bits",
            "Severity: Informational",
            "Difficulty: High",
            "Type: Data Exposure",
        ]
        "body": ...

        """

        # Get the Severity based on finding identifier (C1, H1, M1, L1, etc.)
        severity_phrase = finding.split(" ")[0].strip()
        # Set severity based on the first letter
        match severity_phrase[0]:
            case "C":
                severity = "Critical"
            case "H":
                severity = "High"
            case "M":
                severity = "Medium"
            case "L":
                severity = "Low"
            case "A":
                severity = "Informational"
            case "N":
                severity = "Informational"
            case _:
                return # Skip, this isn't a finding but an artifact of imperfect parsing

        # Get the title and description together, depending on if the title can be parsed
        numbered_title = finding[finding.find(" "):].strip()
        title_phrase = numbered_title[numbered_title.find(" ")+1:].strip()
        if title_phrase.find("STATUS") >= 0:
            title = title_phrase.split("STATUS")[0]
            # Check if parsing error, causing more than one finding in this line, cut to only this finding
            index_description = title_phrase.split("STATUS")[1].lower().find("id description")
            if index_description >= 0:
                description = title_phrase.split("STATUS")[1][:index_description]
            else:
                description = title_phrase.split("STATUS")[1]
        else:
            title = ""
            # Check if parsing error, causing more than one finding in this line, cut to only this finding
            index_description = title_phrase.lower().find("id description")
            if index_description >= 0:
                description = title_phrase[:index_description]
            else:
                description = title_phrase

        protocol = ""
        try:
            # Get the protocol name
            protocol = json_name.split(" _ ")[1]
            if protocol.lower().find(" audit") > 0:
                protocol = protocol[:protocol.lower().find(" audit")]
            else:
                protocol = protocol[:-4] # remove the .txt file extension
        except IndexError:
            continue

        # Calculate proper URL
        url = json_name.replace(" _ ", "/")[:-4] + ".pdf"

        result.append(
            {
                "title": title.encode("ascii", "ignore").decode(),
                "html_url": "https://github.com/dedaub/audits/tree/main/" + url,
                # clean utf-8 characters
                "body": description.encode("ascii", "ignore").decode(),
                "labels": [
                    "Dedaub",
                    protocol.encode("ascii", "ignore").decode(),
                    "Severity: " + severity.encode("ascii", "ignore").decode()
                ]
            }
        )

    # load the existing json file and append the new findings
    try:
        with open("../results/dedaub_findings.json", "r") as f:
            existing_findings = json.load(f)
    except FileNotFoundError:
        existing_findings = []

    with open("../results/dedaub_findings.json", "w") as f:
        json.dump(existing_findings + result, f, indent=4)
        
        
if __name__ == "__main__":

    # Step 1: Extract findings text from PDFs
    for contents in os.walk("../pdfs/dedaub-audits"):
        if contents[1]:
            for subdir in contents[1]:
                pdf_path = contents[0] + "/" + subdir
                for pdf_file in os.listdir(pdf_path):
                    # Skip Ethereum Foundation directory, those are impact studies not audits
                    # Skip DeFi Saver and Mushroom Finance directory, they have very different report structures
                    if pdf_path.find("Ethereum Foundation") < 0 and pdf_path.find("DeFi Saver") < 0 and pdf_path.find("Mushrooms Finance") < 0:
                        try:
                            extract_finding(subdir + "/" + pdf_file)
                        except:
                            print("Error parsing " + pdf_file)

    # Step 2: Parse findings text into JSON
    for json_file in os.listdir("../findings_newupdate/dedaub"):
        jsonify_findings(json_file)

    # Step 3: deduplicate findings
    # only keep unique findings, the file contains an array of findings
    with open("../results/dedaub_findings.json", "r") as f:
        findings = json.load(f)

    unique_findings = []
    for finding in findings:
        if finding not in unique_findings:
            unique_findings.append(finding)

    # Step 4: write only unique findings to final json
    with open("../results/dedaub_findings.json", "w") as f:
        json.dump(unique_findings, f, indent=4)

    