# [Masamune](https://en.wikipedia.org/wiki/Masamune)

![](katana.png) *The smart contract security search utility tool.*

## What is Masamune?

Masamune is a search utility tool that allows you to search for smart contract security vulnerabilities, from a curated list of sources.

To access Masamune, visit [masamune.app](https://masamune.app).

## How does it work?

### Masamune V1.

The search utility is powered by [Lunr.js](https://lunrjs.com/), a full-text search library for the browser.

We have developed custom scrapers for each data source, which are run periodically to retrieve the latest data. You can find the scrapers in the `scrapers` directory.

The data is stored within the `results` directory; for each of the queries, a pattern match is tried against the data, and the results are displayed.

To build locally, just open index.html using a live server, eg. [this extension for VSCode](https://marketplace.visualstudio.com/items?itemName=yandeu.five-server).

### Masamune V2.

The second iteration of Masamune is currently under development, however a beta version will be available at [masamune.app](https://masamune.app) soon. The new version will be powered by [OpenAI's Embeddings](https://platform.openai.com/docs/guides/embeddings) API, which will allow for more advanced search queries, as well as more context aware search results.

## Retrieving the data

Currently, Masamune works on the following data sources:

1. [Code4rena findings](https://code4rena.com/reports).
2. [Immunefi bugfixes](https://github.com/immunefi-team/Web3-Security-Library).
3. [DeFi Hacks Analysis](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b).
4. [Zellic audits](https://github.com/Zellic/publications).
5. [yAudit findings](https://reports.yaudit.dev/).
6. [Trail of Bits audits](https://github.com/trailofbits/publications)
4. Various Gitbooks, such as the [Layer Zero Docs](https://layerzero.gitbook.io), [Curve Finance Docs](https://resources.curve.fi/), [MEV Wiki](https://www.mev.wiki/), etc.
