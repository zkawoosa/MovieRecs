# Zain Kawoosa

from bs4 import BeautifulSoup as bs
from random import randint
import re
import sys
import os
import requests
import time
import pdb

Link_Limit = int(sys.argv[1]) * 10
Header_Info = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'referer': 'https://...', 
    'Content-Type': 'text/html'
}

class Movie:
    def __init__(self, link):
        self.movie_link = link

        # Contains a set of unique actors, writers, directors, etc for a movie
        self.person_set = set()

        # Predefine as -1 to detect if ratings are not found
        self.metascore = -1

        self.imdb_rating = -1

        # self.genres = set()

    def add_person(self, link):
        self.person_set.add(link)

# For a given url, isolate the url up until the title id followed by slash
def isolate_title(url):
    # Split by slashes first
    split = re.split("/", url)
    reformed_url = f"{split[0]}/{split[1]}/{split[2]}/{split[3]}/{split[4]}/"

    # Next check if trailing ?, if so split
    if "?" in reformed_url:
        split_two = re.split("\?", reformed_url)
        return f"{split_two[0]}/"

    return reformed_url

# For a given url, isolate the url up until the name id followed by slash
def isolate_name(url):
    #breakpoint()
    # Split by slashes first
    split = re.split("/", url)
    reformed_url = f"/{split[1]}/{split[2]}/"

    # Next check if trailing ?, if so split
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

def main():
    # Need to define starting point for crawl
    seedUrl = "https://www.imdb.com/title/tt15398776/"

    # Only accept urls that are in certain domains
    ACCEPTED_DOMAINS = ['imdb.com/title/']

    # Set of valid links that lead to movie title pages
    links_identified = set()
    links_identified.add(seedUrl)

    # Queue from which links are pulled for each request
    links_queue = [seedUrl]

    only_session = requests.Session()

    while len(links_identified) < Link_Limit:
        # Pop link from queue
        parent_link = links_queue.pop(0)
        try:
            # Fetching HTML from webpage at parent_link
            current_page = only_session.get(parent_link, timeout=3, headers=Header_Info)
            current_soup = bs(current_page.content, features="html.parser")
            
            # Take discovered links and check validity
            for link_obj in current_soup.find_all('a'):
                # Breaking out of loop once we've identified sufficient links
                if len(links_identified) >= Link_Limit:
                    break

                # Get link, reform it, check domain
                child_link = link_obj.get('href')
                stripped = url_strip(child_link)
                with_domain = "https://www.imdb.com" + stripped
                
                # Check domain
                if url_validate(with_domain, ACCEPTED_DOMAINS):
                    # Isolate the relevant title link
                    isolated_title = isolate_title(with_domain)

                    # Check if visited
                    if not isolated_title in links_identified:
                        # Identify link, add to queue of pages to check
                        links_identified.add(isolated_title)
                        links_queue.append(isolated_title)
                        print(f"Added {isolated_title} to queue. {len(links_identified)}")

        except requests.exceptions.RequestException as e:
            print(f"Error for fetching following link: {parent_link}")
            print(f"Error Message: {e}")

        # Sleep keeps imdb from getting upset
        time.sleep(randint(1,3))

    # List of Movie objects
    movie_list = []

    # Iterate over movies, extract class members
    for movie_link in links_identified:
        try:
            current_page = only_session.get(movie_link, timeout=3, headers=Header_Info)
            current_soup = bs(current_page.content, features="html.parser")    
            
            # Create movie obj
            movie_obj = Movie(movie_link)

            # Find meta score
            metascore_obj = current_soup.find("span", class_="score-meta")
            metascore = metascore_obj.get_text()
            movie_obj.metascore = metascore

            # Find IMDB rating
            imdb_obj = current_soup.find("span", class_="sc-bde20123-1 iZlgcd")
            imdb_rating = imdb_obj.get_text()
            movie_obj.imdb_rating = imdb_rating

            # Find Genres
            # breakpoint()
            # genre_divs = current_soup.find("div", attrs={'datatest-id':'genres'})
            # for div in genre_divs.find_all("span", class_='ipc-chip__text'):
            #     print(div)


            # Take all links, narrow down to links for "names"
            for link_obj in current_soup.find_all('a'):
                link = link_obj.get('href')
                stripped = url_strip(link)

                # Check if link format is right before adding
                if stripped.startswith("/name/"):
                    movie_obj.add_person(f"https://www.imdb.com{isolate_name(stripped)}")
            
            # Add movie obj to list
            movie_list.append(movie_obj)
        except Exception as e:
            print(f"Error Message: {e}")

    # Writing to output file
    with open('crawler.output', 'w') as output:
        for movie in movie_list:
            print(movie.movie_link)
            output.write(f"{movie.movie_link} \n")
            count = 1
            for name_link in movie.person_set:
                output.write(f"{count}.{name_link} \n")
                count += 1


if __name__ == '__main__':
    main()
