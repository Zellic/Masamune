import requests
import json
import math
import os

"""
This script retrieves all the findings from the code-423n4 github organization, and saves them to a json file.
"""


def get_repos(cache):
    """
    Returns a list of all the repositories of code-423n4
    """

    if cache:
        with open('../cache/repos.json', 'r') as f:
            return json.load(f)

    all_repos = []
    page = 0
    while page < 10: # 1000 repos basically
        # TODO: update this so it knows the last updated repo and start from there on...
        repos_api_path = f"https://api.github.com/orgs/code-423n4/repos?per_page=100&page={page}"

        if not os.environ.get('GITHUB_TOKEN'):
            raise Exception("GITHUB_TOKEN not set")
            
        headers = {
            'Authorization': 'token ' + os.environ['GITHUB_TOKEN']
        }

        res = requests.get(
            repos_api_path,
            headers=headers
        ).json()

        print(f"{len(res)} repos found on page {page}")
        all_repos += res

        if len(res) != 100:
            break
            
        page += 1
    
    # if not cache:
    with open('../cache/repos.json', 'w') as f:
        json.dump(all_repos, f)

    return all_repos

def get_repo_info(_repos, cache):
    """
    Returns a dict with all the individual "findings"-repositories and some info about them.
    """

    if cache:
        with open('../cache/repo_info.json', 'r') as f:
            return json.load(f)

    individual_repos = {}
    for _, repo in enumerate(_repos):
        if repo['name'][-8:] == "findings":
            # findings.append(repo)
            individual_repos[repo['name']] = {
                'url': repo['html_url'],
                'issues_url': repo['issues_url'][:-9], # get rid of '{/number}'
                'nr_issues': repo['open_issues']
            }

    if not cache:
        with open('../cache/repo_info.json', 'w') as f:
            json.dump(individual_repos, f)

    return individual_repos

def get_issues(_findings_info, cache):
    """
    Returns a list of all the issues of the findings repos.
    """

    if cache:
        with open('../cache/issues.json', 'r') as f:
            return json.load(f)

    total_found_issues =  []

    for finding in _findings_info:

        issues_url = _findings_info[finding]['issues_url']
        nr_issues = _findings_info[finding]['nr_issues']

        # calculate how many pages required for each finding, max 100 per page
        nr_pages = math.ceil(nr_issues / 100)
        for page in range(1, nr_pages + 1):
            req_url = issues_url + f"?per_page=100&page={page}"

            # set authorization token for github api
            # needed for more than 1 request / sec
            if not os.environ.get('GITHUB_TOKEN'):
                raise Exception("GITHUB_TOKEN not set")
            
            headers = {
                'Authorization': 'token ' + os.environ['GITHUB_TOKEN']
            }

            req = requests.get(req_url, headers=headers).json()

            for issue in req:
                html_url = issue['html_url']
                issue_title = issue['title']
                raw_issue_labels = issue['labels']
                updated_issue_labels = []
                for _label in raw_issue_labels:
                    updated_issue_labels.append(
                        _label['name']
                    )
                found_issue = {
                    'title': issue_title,
                    'html_url': html_url,
                    'labels': updated_issue_labels,
                    'target': finding
                }
                total_found_issues.append(found_issue)

    if not cache:
        with open('../cache/issues.json', 'w') as f:
            json.dump(total_found_issues, f)

    return total_found_issues

def get_issues_text(_issues, cache):
    """
    @param _issues: list of issues, which have the format:
    {'title': 'Unnecessary function calls in `addLiquidity`', 'html_url': 'https://github.com/code-423n4/2021-04-vader-findings/issues/320', 'labels': ['bug', 'G (Gas Optimization)'], 'target': '2021-04-vader-findings'}

    Returns a the text of the issues if the particular issue had one of the following labels:
    "sponsor acknowledged", "2 (Med Risk)", "3 (High Risk)" or "addressed", "sponsor confirmed"
    """

    if cache:
        with open('../cache/issues_text.json', 'r') as f:
            return json.load(f)

    selected_issues = []

    # load the current issues_text.json to know where to continue from:
    with open('../cache/issues_text.json', 'r') as f:
        selected_issues = json.load(f)

    # get the "body" of the last issue in the list
    last_issue_html = selected_issues[-1]['html_url']

    # find the index of the last issue in the _issues list
    last_issue_index = 0

    for index, issue in enumerate(_issues):
        if issue['html_url'] == last_issue_html:
            print("FOUND IT AT INDEX: " + str(index))
            last_issue_index = index
            break

    print("CONTINUE FROM INDEX: " + str(last_issue_index))
    # get the issues from the last issue index
    _issues = _issues[last_issue_index + 1:]
    
    for issue in _issues:
        # if "sponsor acknowledged" in issue['labels'] or "2 (Med Risk)" in issue['labels'] or "3 (High Risk)" in issue['labels'] or "addressed" in issue['labels']:
        if "sponsor confirmed" in issue['labels'] or "addressed" in issue['labels']:
            # get the api path
            api_path = issue['html_url'].replace('https://github.com/', 'https://api.github.com/repos/')
            
            # set authorization token for github api
            # needed for more than 1 request / sec
            if not os.environ.get('GITHUB_TOKEN'):
                raise Exception("GITHUB_TOKEN not set")
            
            headers = {
                'Authorization': 'token ' + os.environ['GITHUB_TOKEN']
            }

            req = requests.get(api_path, headers=headers).json()
            
            try:
                issue['body'] = req['body'].replace("\n", " ").replace("\t", " ")
            except:
                print("HAD TO SKIP AT ISSUE: " + issue['html_url'])
                # break

                # TODO Figure if the break before was due to 
                # GITHUB API rate limit or something else.
                continue 

            issue['target'] = issue['target']

            selected_issues.append(issue)

    with open('../cache/issues_text.json', 'w') as f:
        # overwrite existing file
        json.dump(selected_issues, f)

    return selected_issues

def save_to_codearena_findings(_issues):
    """
    Saves the issues to the codearena_findings.json file.
    """
    with open('../results/codearena_findings.json', 'w') as f:
        json.dump(_issues, f)

def main():

    # by default
    cache = True

    print("Step 1: Getting all the repositories...")
    all_repos = get_repos(cache)

    print("Step 2: Getting all the findings repositories...")
    findings_info = get_repo_info(all_repos, cache)

    print("Step 3: Getting all the issues of the findings repositories...")
    all_findings_issues = get_issues(findings_info, cache)

    print("Step 4: Getting the text of the issues...")
    selected_issues = get_issues_text(all_findings_issues, cache)

    print("Step 5: Saving the issues to the codearena_findings.json file...")
    save_to_codearena_findings(selected_issues)
    

if __name__ == "__main__":
    main()