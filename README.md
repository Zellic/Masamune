# [Masamune](https://en.wikipedia.org/wiki/Masamune)

![](katana.png) *The smart contract security search utility tool.*

## What is Masamune?

Masamune is a search utility tool that allows you to search for smart contract security vulnerabilities, from a curated list of sources.

To access Masamune, visit [masamune.app](https://masamune.app).

## How does it work?

The search utility is powered by [Lunr.js](https://lunrjs.com/), a full-text search library for the browser.

We have developed custom scrapers for each data source, which are run periodically to retrieve the latest data. You can find the scrapers in the `scrapers` directory.

The data is stored within the `results` directory; for each of the queries, a pattern match is tried against the data, and the results are displayed.

To build locally, just open index.html using a live server, eg. [this extension for VSCode](https://marketplace.visualstudio.com/items?itemName=yandeu.five-server).

### Retrieving the data

Currently, Masamune works on the following data sources:

1. [Code4rena findings](https://code4rena.com/reports).
2. [Immunefi bugfixes](https://github.com/immunefi-team/Web3-Security-Library).
3. [DeFi Hacks Analysis](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b).
4. Various Gitbooks, such as the [Layer Zero Docs](https://layerzero.gitbook.io), [Curve Finance Docs](https://resources.curve.fi/), [MEV Wiki](https://www.mev.wiki/), etc.

### Creating a custom scraper

To add a new data source, a custom scraper for the report format must be created. Existing examples are found in the `scrapers` directory.

Scrapers have 2 main functions. The `extract_finding()` function parses the report files and stores the stored output in a text file in the `findings_newupdate` directory. The `jsonify_findings()` function parses this text file and outputs a JSON file stored in the `results` directory. The format of the JSON data is found in other scraper files but generally follows this format:

```
        "title": "MobileCoin Foundation could infer token IDs in certain scenarios",
        "labels": [
            "Trail of Bits",
            "Severity: Informational",
            "Difficulty: High",
            "Type: Data Exposure",
        ]
        "description": ...
```

After the new scraper is created and the JSON output is stored in the `results` directory, the JSON file must be added to the `dataset` variable in logic.js to be included in the search results.

### Credits:

> Original repository: [ippsec.rocks](https://github.com/IppSec/ippsec.github.io/)

> Katana designer: [noob.art](https://noobart.work/)


> <img src="zellic-logo-blue-transparent.png" width="7%" height="7%"> Zellic team: [zellic.io](https://zellic.io/) 
