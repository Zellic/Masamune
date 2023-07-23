# Parse Trail Of Bits generic format pdf audits via the pdfminer.six library
from pdfminer.high_level import extract_text
import re
import os
import json


def extract_finding(pdf_path):
    text = extract_text(pdf_path)
    pdf_name = pdf_path.split("/")[-1]
    print(pdf_name)

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
        print("Error parsing " + pdf_name)
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
    print("Length: " + str(len(finding_titles)))

    # text_findings = "\n".join([x for x in text_findings.splitlines() if re.match(r' ID Descrip\S+', x) or re.match(r' Id Descrip\S+', x) or re.match(r' Nr. Descrip\S+', x)])

    # try:
    #     text = text.split("Description:")[1]
    # except IndexError:
    #     with open("dedaub_parser_errors.txt", "a") as f:
    #         f.write(pdf_name + "\n")
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
            f.write(pdf_name + "\n")
            return

    # Save the findings to a file
    with open(f"../findings_newupdate/dedaub/{pdf_name[:-4]}.txt", "w") as f:
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
        L1 Inconsistent use of price feeds for the price of the underlyin STATUS DISMISSED The BeyondPrice contract gets the price of the underlying token via the function _getUnderlyingPrice(), which consults a Chainlink price feed for the price. // BeyondPrice::_getUnderlyingPrice function _getUnderlyingPrice(address underlying, address _strikeAsset) internal view returns (uint256) { } return PriceFeed(protocol.priceFeed()). getNormalizedRate(underlying, _strikeAsset); However, when trying to obtain the same price in the function _getCollateralRequirements(), the addressBook is used to get the price feed from an Oracle implementing the IOracle interface. // BeyondPrice::_getCollateralRequirements function getCollateralRequirements( Types.OptionSeries memory _optionSeries, uint256 _amount ) internal view returns (uint256) { IMarginCalculator marginCalc = IMarginCalculator(addressBook.getMarginCalculator()); return marginCalc.getNakedMarginRequired(  _optionSeries.underlying, _optionSeries.strikeAsset, _optionSeries.collateral, _amount / SCALE_FROM, _optionSeries.strike / SCALE_FROM, // assumes in e18 IOracle(addressBook.getOracle()).getPrice(_optionSeries.underlying), _optionSeries.expiration, 18, // always have the value return in e18 _optionSeries.isPut ); } The same addressBook technique is used in the getCollateral() function of the OptionRegistry contract and in the checkVaultHealth() function of the Option registry contract. It is recommended that this is refactored to use the Chainlink feed in order to avoid a situation where dierent prices for the underlying are obtained by dierent parts of the code. The Rysk team intends to keep the price close to what the Opyn system would quote, thus using the Opyn chainlink oracle is actually correct as it represents the actual situation that would occur for these given quotes L2 Multiple uses of div before mul in OptionExchanges _handleDHVBuyback() function RESOLVED In the OptionExchange contracts _handleDHVBuyback() function, a division is used before a multiplication operation at lines 925 and 932. It is recommended to use multiplication prior to division operations to avoid a possible loss of precision in the calculation. Alternatively, the mulDiv function of the PRBMath library could be used.  CENTRALIZATION ISSUES: It is often desirable for DeFi protocols to assume no trust in a central authority, including the protocols owner. Even if the owner is reputable, users are more likely to engage with a protocol that guarantees no catastrophic failure even in the case the owner gets hacked/compromised. We list issues of this kind below. (These issues should be considered in the context of usage/deployment, as they are not uncommon. Several high-prole, high-value protocols have signicant centralization threats.) ID Description N1 Centralized Implied Volatility Updates STATUS ACKNOWLEDGED The implied volatility used by the BeyondPricer contract to price options is determined by the SABR model. However, the SABR model is a function of several parameters set by bots controlled by the Rysk team. This means that the Rysk team has the ability to aect option prices through the control of these parameters. The Rysk team has acknowledged the issue and has stated that the decentralization of the implied volatility computation is not currently feasible but will be part of their progressive decentralization eorts.  OTHER / ADVISORY ISSUES: This section details issues that are not thought to directly aect the functionality of the project, but we recommend considering them. ID Description STATUS

        We want to extract the following:
        "title": "Inconsistent use of price feeds for the price of the underlyin",
        "html_url": "https://github.com/Dedaub/audits/blob/main/Rysk/Rysk%20Audit%20-%20Feb%20'23.pdf",
        "body": "The BeyondPrice contract gets the price of the underlying token via the function _getUnderlyingPrice(), which consults a Chainlink price feed for the price. // BeyondPrice::_getUnderlyingPrice function _getUnderlyingPrice(address underlying, address _strikeAsset) internal view returns (uint256) { } return PriceFeed(protocol.priceFeed()). getNormalizedRate(underlying, _strikeAsset); However, when trying to obtain the same price in the function _getCollateralRequirements(), the addressBook is used to get the price feed from an Oracle implementing the IOracle interface. // BeyondPrice::_getCollateralRequirements function getCollateralRequirements( Types.OptionSeries memory _optionSeries, uint256 _amount ) internal view returns (uint256) { IMarginCalculator marginCalc = IMarginCalculator(addressBook.getMarginCalculator()); return marginCalc.getNakedMarginRequired(  _optionSeries.underlying, _optionSeries.strikeAsset, _optionSeries.collateral, _amount / SCALE_FROM, _optionSeries.strike / SCALE_FROM, // assumes in e18 IOracle(addressBook.getOracle()).getPrice(_optionSeries.underlying), _optionSeries.expiration, 18, // always have the value return in e18 _optionSeries.isPut ); } The same addressBook technique is used in the getCollateral() function of the OptionRegistry contract and in the checkVaultHealth() function of the Option registry contract. It is recommended that this is refactored to use the Chainlink feed in order to avoid a situation where dierent prices for the underlying are obtained by dierent parts of the code. The Rysk team intends to keep the price close to what the Opyn system would quote, thus using the Opyn chainlink oracle is actually correct as it represents the actual situation that would occur for these given quotes L2 Multiple uses of div before mul in OptionExchanges _handleDHVBuyback() function RESOLVED In the OptionExchange contracts _handleDHVBuyback() function, a division is used before a multiplication operation at lines 925 and 932. It is recommended to use multiplication prior to division operations to avoid a possible loss of precision in the calculation. Alternatively, the mulDiv function of the PRBMath library could be used.  CENTRALIZATION ISSUES: It is often desirable for DeFi protocols to assume no trust in a central authority, including the protocols owner. Even if the owner is reputable, users are more likely to engage with a protocol that guarantees no catastrophic failure even in the case the owner gets hacked/compromised. We list issues of this kind below. (These issues should be considered in the context of usage/deployment, as they are not uncommon. Several high-prole, high-value protocols have signicant centralization threats.) ",
        "labels": [
            "Dedaub",
            "Rysk",
            "Severity: Low",
        ]

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
                print(description)
            else:
                description = title_phrase.split("STATUS")[1]
        else:
            title = ""
            # Check if parsing error, causing more than one finding in this line, cut to only this finding
            index_description = title_phrase.lower().find("id description")
            if index_description >= 0:
                description = title_phrase[:index_description]
                print(description)
            else:
                description = title_phrase

        protocol = ""
        try:
            # Get the protocol name
            if json_name.lower().find(" audit") > 0:
                protocol = json_name[:json_name.lower().find(" audit")]
            else:
                protocol = json_name[:-4] # remove the .txt file extension
        except IndexError:
            continue

        result.append(
            {
                "title": title.encode("ascii", "ignore").decode(),
                "html_url": "https://github.com/dedaub/audits/tree/main/",
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
    # pdf_names = []
    # for contents in os.walk("../pdfs/dedaub-audits"):
    #     if contents[1]:
    #         for subdir in contents[1]:
    #             pdf_path = contents[0] + "/" + subdir
    #             for pdf_file in os.listdir(pdf_path):
    #                 # Skip Ethereum Foundation directory, those are impact studies not audits
    #                 # Skip DeFi Saver and Mushroom Finance directory, they have very different report structures
    #                 if pdf_path.find("Ethereum Foundation") < 0 and pdf_path.find("DeFi Saver") < 0 and pdf_path.find("Mushrooms Finance") < 0:
    #                     extract_finding(pdf_path + "/" + pdf_file)
    #                     pdf_names.append(pdf_file)

    # Step 2: Parse findings text into JSON
    for json_file in os.listdir("../findings_newupdate/dedaub"):
        jsonify_findings(json_file)

    # Step 3: deduplicate findings
    # only keep unique findings, the file contains an array of findings
    # with open("../results/dedaub_findings.json", "r") as f:
    #     findings = json.load(f)

    # unique_findings = []
    # for finding in findings:
    #     if finding not in unique_findings:
    #         unique_findings.append(finding)

    # Step 4: write only unique findings to final json
    # with open("../results/dedaub_findings.json", "w") as f:
    #     json.dump(unique_findings, f, indent=4)

    