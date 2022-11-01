"""
This script enumerates all documented hacks in the DeFiHackLabs repository. (from the notion.so accompanying page)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import json
import math
import os
import time

def get_divs(_page):
    """
    Returns a list of all the div within a web page that contain have the "notion-selectable notion-page-block notion-collection-item" class.
    """

    # Use selenium to retrieve all the inspect element of the page; the content is dynamically loaded, so simply the requests library won't work.
    driver = webdriver.Firefox()
    driver.get(_page)

    # keep scrolling down until there are more than 100 elements found by driver.find_elements
    while len(driver.find_elements(By.CLASS_NAME, "notion-collection-item")) < 100:
        # NOTE click on the page with the mouse so that the PAGE_DOWN works
        # TODO automate the clicking / find a better way to scroll down

        # NOTE window.scrollTo doesn't work because the height of the page is dynamic, we need to scroll with DOWN key instead
        driver.find_element(By.CLASS_NAME, "notion-body").send_keys(Keys.PAGE_DOWN)

        time.sleep(5)

    # get all loaded elements
    content_elements = driver.find_elements(By.CLASS_NAME, "notion-collection-item")

    # beautify the result
    beautified_results = []

    for result in content_elements:
        # split the result into a list
        result = result.text.split("\n")

        # create a dict from the list
        result_dict = {}
        # the first few elements until a number is reached is the "labels" section
        i = 0
        while result[i][0] != "2":
            i += 1
        result_dict["labels"] = result[:i]

        # the next element is the "Date" section
        result_dict["date"] = result[i][:4] + "." + result[i][4:6] + "." + result[i][6:]
        i += 1

        # the next element is the "Project" section
        result_dict["title"] = result[i]

        # also add it as target
        result_dict["target"] = "[HACKED] " + result[i]
        i += 1

        # skip the description
        i += 1

        # the next element is the "Amount" section
        if result[i][0] !=  "h": # some don't have amount
            result_dict["amount"] = result[i]
            i += 1

        try:
            result_dict["html_url"] = result[i]
        except IndexError: # no link
            pass

        beautified_results.append(result_dict)

    driver.quit()

    # add each result to the `all_findings_issues.json` file
    with open("all_findings_issues.json", "r") as f:
        all_findings_issues = json.load(f)

    for result in beautified_results:
        all_findings_issues.append(result)

    with open("all_findings_issues.json", "w") as f:
        json.dump(all_findings_issues, f)

if __name__ == "__main__":
    get_divs("https://wooded-meter-1d8.notion.site/0e85e02c5ed34df3855ea9f3ca40f53b?v=22e5e2c506ef4caeb40b4f78e23517ee")