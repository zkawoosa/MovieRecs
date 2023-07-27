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

# Remove http://, https://, trailing slashes
def url_strip(url):
    # Removing any leading http:// or https://
    stripped_url = re.compile(r"https?://(www\.)?").sub("", url)
    # Removing trailing backslashes
    stripped_url = re.compile("\/$").sub("", stripped_url)
    return stripped_url

# Checks if the URL is in set of identified urls
def url_identified(url, links_identified):
    if url_strip(url) in links_identified:
        return True
    else:
        return False

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
    links_identified = set(seedUrl)
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
                        # Check if visited
                        if not url_identified(with_domain, links_identified):
                            # Adding stripped version of link to identified set
                            cleaned_link = with_domain
                            links_identified.add(cleaned_link)
                            # Adding link to be opened
                            links_queue.append(cleaned_link)
                            
                            print(f"Added {cleaned_link} to queue.")

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
