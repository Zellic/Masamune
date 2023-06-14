var searchResultFormat = '<tr><td><a href="$link" target="_blank">$target</a></td><td align="left">$title</td><td>$labels</td></tr>';
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
    updateResults: function(loc, results) {
        
        // Print the number of results

        if (results.length == 0) {
            noResults.style.display = '';

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

                let body = r.metadata.body;
                let title = r.metadata.title;
                let url = r.metadata.html_url;
                let labels = r.metadata.labels;
                let target = r.metadata.target;

                let labelString = '';
                for (let i = 0; i < labels.length; i++) {
                    labelString += labels[i];
                    if (i != labels.length - 1) {
                        labelString += ', ';
                    }
                }

                el = searchResultFormat
                    .replace('$target', target ? target : title) // if r.target is not available, use r.title
                    .replace('$title', target ? title : body.substring(0, 400) + '...') 
                    .replace('$link', url)
                    .replace('$labels', labelString);
                
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

    
    async function doSearch(event) {
        var val = searchValue.value;
    
        if (val != '') {
            const response = await fetch(`http://127.0.0.1:5000/search?query=${val}`);
            const data = await response.json();
            controls.displayResults();
            window.controls.setColor(colorUpdate, data.results.length == 0 ? 'no-results' : 'results-found');
            window.controls.updateResults(resultsTable, data.results);
        } else {
            controls.hideResults();
            window.controls.setColor(colorUpdate, 'no-search');
            noResults.style.display = 'none';
        }
    
    }

    // default to no results
    window.controls.updateResults(resultsTable, []);

    form.submit(doSearch);

    // wait for the user to stop typing for 500ms before searching
    var typingTimer;
    searchValue.addEventListener('keyup', function() {
        clearTimeout(typingTimer);

        typingTimer = setTimeout(doSearch, 500);

    });
});
