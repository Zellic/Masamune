"""
This script enumerates all code-423n4's findings repositories.
"""
import requests
import json
import math
import os

def get_repos():
    """
    Returns a list of all the repositories of code-423n4
    """
    all_repos = []
    page = 0
    while page < 10: # 1000 repos basically
        # TODO: update this so it knows the last updated repo and start from there on...
        
        repos_api_path = f"https://api.github.com/orgs/code-423n4/repos?per_page=100&page={page}"
        page += 1
        res = requests.get(repos_api_path).json()
        all_repos += res
    return all_repos

def get_repo_info(_repos):
    """
    Returns a dict with all the individual "findings"-repositories and some info about them.
    """
    individual_repos = {}
    for _, repo in enumerate(_repos):
        if repo['name'][-8:] == "findings":
            # findings.append(repo)
            individual_repos[repo['name']] = {
                'url': repo['html_url'],
                'issues_url': repo['issues_url'][:-9], # get rid of '{/number}'
                'nr_issues': repo['open_issues']
            }
    return individual_repos

def save_findings_info(_filename, _findings_info):
    """
    Saves the findings info to a json file.
    """
    with open(f'{_filename}.json', 'w') as f:
        json.dump(_findings_info, f)

def load_findings_info(_findings_filename):
    """
    Loads the findings info from a json file.
    """
    with open(_findings_filename, 'r') as f:
        return json.load(f)

def get_issues(_findings_info):
    """
    Returns a list of all the issues of the findings repos.
    """
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

                """

                TODO: add option to only add 'Confirmed' labelled issues to the dataset;
                or create a separate dataset altogether

                Valid labels:
                id = "2879876984" -> 1 (Low Risk)
                id = "2877268383" -> 2 (Med Risk)
                id = "2878045993" -> 3 (High Risk)
                id = "2984571655" -> G (Gas Optimization)

                Labels structure:
                'labels': [
                    {
                        'id': 2876959822, 
                        'node_id': 'MDU6TGFiZWwyODc2OTU5ODIy', 
                        'url': 'https://api.github.com/repos/code-423n4/2021-04-marginswap-findings/labels/bug', 
                        'name': 'bug', 
                        'color': 'BFD4F2', 
                        'default': True, 
                        'description': "Something isn't working"
                    }, 
                    {
                        'id': 2879876984, 
                        'node_id': 'MDU6TGFiZWwyODc5ODc2OTg0', 
                        'url': 'https://api.github.com/repos/code-423n4/2021-04-marginswap-findings/labels/1%20(Low%20Risk)',
                        'name': '1 (Low Risk)',
                        'color': '1D76DB', 
                        'default': False, 
                        'description': ''
                        }
                ]
                """

    return total_found_issues

def main():
    # all_findings_issues = load_findings_info('all_findings_issues.json')
    # print(all_findings_issues)
    # print(len(all_findings_issues))
    all_repos = get_repos()
    findings_info = get_repo_info(all_repos)
    # save_findings_info('all_findings_issues.json', findings_info)
    all_findings_issues = get_issues(findings_info)
    save_findings_info('all_findings_issues', all_findings_issues)
    

if __name__ == "__main__":
    main()