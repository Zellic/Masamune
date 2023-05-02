# [Masamune](https://en.wikipedia.org/wiki/Masamune)

![](katana.png) *The smart contract security search utility tool.*

## What is Masamune?

Masamune is a search utility tool that allows you to search for smart contract security vulnerabilities, from a curated list of sources.

To access Masamune, visit [masamune.app](https://masamune.app).

## How does it work?

Masamune is a static site, built with [Jekyll](https://jekyllrb.com/), and hosted on [Github Pages](https://pages.github.com/).

The search utility is powered by [Lunr.js](https://lunrjs.com/), a full-text search library for the browser.

We have developed custom scrapers for each data source, which are run periodically to retrieve the latest data. You can find the scrapers in the `scrapers` directory.

The data is stored within the `results` directory; for each of the queries, a pattern match is tried against the data, and the results are displayed.

### Retrieving the data

Currently, Masamune works on the following data sources:

1. [Code4rena findings](https://code4rena.com/reports).
2. [Immunefi bugfixes](https://github.com/immunefi-team/Web3-Security-Library).
3. [DeFi Hacks Analysis](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b).

### Credits:

> Original repository: [ippsec.rocks](https://github.com/IppSec/ippsec.github.io/)

> Katana designer: [noob.art](https://noobart.work/)


> <img src="zellic-logo-blue-transparent.png" width="7%" height="7%"> Zellic team: [zellic.io](https://zellic.io/) 
