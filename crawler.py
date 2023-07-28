# Zain Kawoosa
# zkawoosa
# crawler.py
# PURPOSE: Collects movie URLs from IMDB
from bs4 import BeautifulSoup as bs
from random import randint
import re
import sys
import os
import requests
import time
import pdb

# For a given url, isolate the url up until the title id followed by slash
# https://www.imdb.com/title/tt15398776/fullcredits/cast?ref_=tt_ov_st_sm
def isolate_title(url):
    # Split by slashes first
    split = re.split("/", url)
    # Next check if trailing ?, if so split
    reformed_url = f"{split[0]}/{split[1]}/{split[2]}/{split[3]}/{split[4]}/"
    if "?" in reformed_url:
        split_two = re.split("\?", reformed_url)
        return f"{split_two[0]}/"
    return reformed_url

# Remove http://, https://, trailing slashes
def url_strip(url):
    # Removing any leading http:// or https://
    stripped_url = re.compile(r"https?://(www\.)?").sub("", url)
    # Removing trailing backslashes
    stripped_url = re.compile("\/$").sub("", stripped_url)
    return stripped_url

# Strip url, check if stripped URL is in domain
def url_validate(url, accepted_domains):
    url = url_strip(url)
    for domain in accepted_domains:
        if url.startswith(domain):
          return True
    return False

# Check if URL redirects to another URL, if true return the final URL
def url_redirect_check(url):
    response = requests.head(url, allow_redirects=True)
    if response.history:
        return True, response.url
    else:
        return False, None


def main():
    # Start with oppenheimer
    seedUrl = "https://www.imdb.com/title/tt15398776/"
    # Only accept urls that are in domain
    ACCEPTED_DOMAINS = ['imdb.com/title/']

    # Set of valid links that lead to movie title pages
    links_identified = set()
    links_identified.add(seedUrl)
    # Queue from which links are pulled for each request
    links_queue = [seedUrl]

    get_session = requests.Session()

    while len(links_identified) < 1000:
        # Pop link from queue
        parent_link = links_queue.pop(0)
        try:
            # Sleep keeps imdb from getting upset
            time.sleep(randint(1,4))
            # Fetching HTML from webpage at parent_link
            response = get_session.get(parent_link, timeout=2, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
            })

            # Checking if page is HTML
            parser = bs(response.content, "html.parser")
            discovered_links = parser.find_all('a')

            for link_obj in discovered_links:
                child_link = link_obj.get('href')
                stripped = url_strip(child_link)
                with_domain = "https://www.imdb.com" + stripped
                #print(with_domain)
                # Check if NoneType
                if with_domain:
                    # Check domain
                    if url_validate(with_domain, ACCEPTED_DOMAINS):
                        isolated_title = isolate_title(with_domain)
                        # Check if visited
                        if not isolated_title in links_identified:
                            links_identified.add(isolated_title)
                            # Adding link to be opened
                            links_queue.append(isolated_title)
                            print(f"Added {isolated_title} to queue. {len(links_identified)}")

                        # Breaking out of loop once we've identified a variable amount of links
                        if len(links_identified) == 1000:
                            break

        except requests.exceptions.RequestException as e:
            print("Error for fetching following link: ", parent_link)
            print("Error Message:")
            print(e)

    # Writing to output file
    with open('crawler.output', 'w') as output:
        for link in links_identified:
            output.write(link + '\n')

if __name__ == '__main__':
    main()
