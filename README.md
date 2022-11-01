# [Masamune](https://en.wikipedia.org/wiki/Masamune)

![](katana.png) *The smart contract security search utility tool.*

### Updating the code4rena datasets via `kanto.py`:

1. Retrieves all repositories from the [code4rena GitHub organization](https://github.com/orgs/code-423n4).

2. Select the repositories that end with `-findings`.

3. Retrieve all the issues from the subsequent `-findings` repositories.

### Adding the previous hacks via `shikoku.py`:

1. Lists all hacks that have been added to this [page](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b?v=22e5e2c506ef4caeb40b4f78e23517ee).

2. Scrapes the page, retrieving the labels, title, etc. 

3. Adds everything as new entries to the `all_findings_issues.json`.

### Search based on the title + "target" or "labels" of the findings.

> Note: for now, Masamune handles findings from the code4rena contests, as well as some previous hacks(listed [here](https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b?v=22e5e2c506ef4caeb40b4f78e23517ee) ).

### What's next?

I aim to create a huuuge dataset from all the existing audits of most reliable security audit companies and organize them in a similar manner. Let's boost smart contract security. Want to help with that? Message me on [Twitter](https://twitter.com/VladToie).

### Credits:

> Original repository: [ippsec.rocks](https://github.com/IppSec/ippsec.github.io/)

> Katana designer: [noob.art](https://noobart.work/)