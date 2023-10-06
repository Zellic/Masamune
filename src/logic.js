var searchResultFormat = '<tr><td><a href="$link" target="_blank">$target</a></td><td align="left">$title</td><td>$tag</tr>';
var totalLimit = 750;

var controls = {
    oldColor: '',
    displayResults: function() {
        if (results.style) {
            results.style.display = '';
        }
        resultsTableHideable.classList.remove('hide');
    },
    hideResults: function() {
        if (results.style) {
            results.style.display = 'none';
        }
        resultsTableHideable.classList.add('hide');
    },
    doSearch: function(match, dataset) {
        results = [];

        words = match.toLowerCase();
        words = words.split(' ');
        regex = '';
        posmatch = [];
        negmatch= [];
        // Lazy way to create regex (?=.*word1)(?=.*word2) this matches all words.
        for (i = 0; i < words.length; i++) {
            if (words[i][0] != '-') {
                posmatch.push(words[i]);
                regex += '(?=.*' + words[i] + ')';
            } else {
                negmatch.push(words[i].substring(1));
                //regex += '(^((?!' + words[i].substring(1) + ').)*$)';
            }
        }
        if (negmatch.length > 0 ) {
          regex += '(^((?!('; // + words[i].substring(1) + ').)*$)';
          for (i= 0; i < negmatch.length; i++) {
            regex += negmatch[i];
            if (i != negmatch.length -1) {
              regex += '|';
            }
          }
        regex += ')).)*$)';
        }

        dataset.forEach(e => {
            // this goes the same, just as for dataset title and target this basically checks the regex against the fields from the dataset entries
            // concatenate e.labels
            var labels = '';
            e.labels.forEach(t => {
                labels += t + ' ';
            });
                
            // TODO how can this be more efficient?
            if ((e.title + e.target + labels /*+ e.body*/).toLowerCase().match(regex)) {
                // e.body is too slow to search through, so it's not included in this version anymore
                results.push(e);
            }

        });
        return results;
    },
    updateResults: function(loc, results) {
        if (results.length == 0) {
            noResults.style.display = '';
            noResults.textContent = 'No Results Found';

            resultsTableHideable.classList.add('hide');
        } else if (results.length > totalLimit) {
            noResults.style.display = '';
            resultsTableHideable.classList.add('hide');
            noResults.textContent = 'Error: ' + results.length + ' results were found, try being more specific';
            this.setColor(colorUpdate, 'too-many-results');
        } else {
            var tableRows = loc.getElementsByTagName('tr');
            for (var x = tableRows.length - 1; x >= 0; x--) {
                loc.removeChild(tableRows[x]);
            }

            noResults.style.display = 'none';
            resultsTableHideable.classList.remove('hide');

            results.forEach(r => {


                let labels = r.labels;
                
                // concatenate all labels into a single string
                let labelString = '';
                for (let i = 0; i < labels.length; i++) {
                    labelString += labels[i];
                    if (i != labels.length - 1) {
                        labelString += ', ';
                    }
                }

                el = searchResultFormat
                    .replace('$target', r.target ? r.target : r.title) // if r.target is not available, use r.title
                    .replace('$title', r.target ? r.title : r.body.substring(0, 400) + '...')
                    .replace('$link', r.html_url)
                    .replace('$tag', labelString);

                // TODO highlight the APPROVED issues' labels

                var wrapper = document.createElement('table');
                wrapper.innerHTML = el;
                var div = wrapper.querySelector('tr');

                loc.appendChild(div);
            });
        }
    },
    setColor: function(loc, indicator) {
        if (this.oldColor == indicator) return;
        var colorTestRegex = /^color-/i;

        loc.classList.forEach(cls => {
            //we cant use class so we use cls instead :>
            if (cls.match(colorTestRegex)) loc.classList.remove(cls);
        });
        loc.classList.add('color-' + indicator);
        this.oldColor = indicator;
    }
};
window.controls = controls;

document.addEventListener('DOMContentLoaded', function() {
    results = document.querySelector('div.results');
    searchValue = document.querySelector('input.search');
    form = document.querySelector('form.searchForm');
    resultsTableHideable = document.getElementsByClassName('results-table').item(0);
    resultsTable = document.querySelector('tbody.results');
    resultsTable = document.querySelector('tbody.results');
    noResults = document.querySelector('div.noResults');
    colorUpdate = document.body;

    // Preventing initial fade
    document.body.classList.add('fade');

    var currentSet = [];

    function doSearch(event) {
        var val = searchValue.value;

        if (val != '') {
            controls.displayResults();
            currentSet = window.dataset;

            currentSet = window.controls.doSearch(val, currentSet);
            if (currentSet.length < totalLimit) window.controls.setColor(colorUpdate, currentSet.length == 0 ? 'no-results' : 'results-found');

            window.controls.updateResults(resultsTable, currentSet);
        } else {
            controls.hideResults();
            window.controls.setColor(colorUpdate, 'no-search');
            noResults.style.display = 'none';
            currentSet = window.dataset;
        }

        if (event.type == 'submit') event.preventDefault();
    }

    
    // fetch all the .json files(immunefi_findings.json, hacklabs_findings.json, codearena_findings.json) and concatenate them into a single array
    // then update the results table with the new dataset
    const fetchAll = async () => {
        const immunefi = await fetch('./results/immunefi_findings.json');
        const immunefiJson = await immunefi.json();

        const hacklabs = await fetch('./results/hacklabs_findings.json');
        const hacklabsJson = await hacklabs.json();

        const codearena = await fetch('./results/codearena_findings.json');
        const codearenaJson = await codearena.json();

        // const gitbook_docs = await fetch('./results/gitbook_docs.json');
        // const gitbook_docsJson = await gitbook_docs.json();

        const tob = await fetch('./results/tob_findings.json');
        const tobJson = await tob.json();

        const yaudit = await fetch('./results/yaudit_findings.json');
        const yauditJson = await yaudit.json();

        const spearbit = await fetch('./results/spearbit_findings.json');
        const spearbitJson = await spearbit.json();

        const openzeppelin = await fetch('./results/openzeppelin_findings.json');
        const openzeppelinJson = await openzeppelin.json();

        const slowmist = await fetch('./results/slowmist_findings.json');
        const slowmistJson = await slowmist.json();

        const halborn = await fetch('./results/halborn_findings.json');
        const halbornJson = await halborn.json();

        const certora = await fetch('./results/certora_findings.json');
        const certoraJson = await certora.json();

        const chainsecurity = await fetch('./results/chainsecurity_findings.json');
        const chainsecurityJson = await chainsecurity.json();

        const consensys = await fetch('./results/consensys_findings.json');
        const consensysJson = await consensys.json();

        const leastauthority = await fetch('./results/leastauthority_findings.json');
        const leastauthorityJson = await leastauthority.json();

        const oak_security = await fetch('./results/oak_security_findings.json');
        const oak_securityJson = await oak_security.json();

        const dataset = immunefiJson.concat(hacklabsJson, codearenaJson, /*gitbook_docsJson,*/ tobJson, yauditJson, spearbitJson, openzeppelinJson, slowmistJson, halbornJson, certoraJson, chainsecurityJson, consensysJson, leastauthorityJson, oak_securityJson);
        window.dataset = dataset;
        currentSet = window.dataset;
        window.controls.updateResults(resultsTable, window.dataset);
        doSearch({ type: 'none' });
    }

    fetchAll(); // TODO [LOL]: it works to not display the table due to this erroring out.

    form.submit(doSearch);

    // wait for the user to stop typing for 500ms before searching
    var typingTimer;
    searchValue.addEventListener('keyup', function() {
        clearTimeout(typingTimer);

        typingTimer = setTimeout(doSearch, 500);

    });
});
