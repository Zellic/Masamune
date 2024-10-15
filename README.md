# [Masamune](https://en.wikipedia.org/wiki/Masamune)

![](img/katana.png) *The smart contract security search utility tool.*

## What is Masamune?

Masamune is a search utility tool that allows you to search for smart contract security vulnerabilities, from a curated list of sources.

To access Masamune, visit [masamune.app](https://masamune.app).

## How does it work?

### Masamune V1.

The search utility is powered by [Lunr.js](https://lunrjs.com/), a full-text search library for the browser.

We have developed custom scrapers for each data source, which are run periodically to retrieve the latest data. 

The data is stored within the `results` directory; for each of the queries, a pattern match is tried against the data, and the results are displayed.

To build locally, just open `index.html` using a live server, eg. [this extension for VSCode](https://marketplace.visualstudio.com/items?itemName=yandeu.five-server).

### Masamune V2.

Beta version is available at [masamune.app](https://masamune.app/new_index.html). V2 is powered by the [OpenAI's Embeddings](https://platform.openai.com/docs/guides/embeddings) API, which allows for more advanced search queries, as well as more context aware search results. Currently, the `text-embedding-3-large` model is in use.

## Retrieving the data

Currently, Masamune works on the following data sources:

1. [Zellic](https://github.com/Zellic/publications)
2. [Code4rena findings](https://code4rena.com/reports)
3. [DeFi Hacks Analysis](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b)
4. [Immunefi bugfixes](https://github.com/immunefi-team/Web3-Security-Library)
5. [yAudit](https://reports.yaudit.dev/)
6. [Trail of Bits](https://github.com/trailofbits/publications)
7. Various Gitbooks, such as the [Layer Zero Docs](https://layerzero.gitbook.io), [Curve Finance Docs](https://resources.curve.fi/), [MEV Wiki](https://www.mev.wiki/), etc
8. [Certora](https://www.certora.com/reports)
9. [Consensys](https://diligence.consensys.io/audits/)
10. [Dedaub](https://github.com/Dedaub/audits/)
11. [Halborn](https://github.com/HalbornSecurity/PublicReports)
12. [Least Authority](https://leastauthority.com/security-consulting/published-audits/)
13. [Oak Security](https://github.com/oak-security/audit-reports/)
14. [SlowMist](https://github.com/slowmist/Knowledge-Base/tree/master/open-report-V2/smart-contract/)
15. [OpenZeppelin](https://blog.openzeppelin.com/tag/security-audits)
16. [Spearbit](https://github.com/spearbit/portfolio/)
17. [ChainSecurity](https://www.chainsecurity.com/smart-contract-audit-reports)
