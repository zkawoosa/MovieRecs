# Zain Kawoosa

from bs4 import BeautifulSoup as bs
from random import randint
import re
import sys
import os
import requests
import time
import pdb

# Collect 10x + 1, where x is the number of results desired by the user
desired_results = int(sys.argv[1])
Link_Limit = desired_results * 10 + 1
Header_Info = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'referer': 'https://...', 
    'Content-Type': 'text/html'
}

class Movie:
    def __init__(self, link):
        self.movie_link = link

        self.title = ""

        # Contains a set of unique actors, writers, directors, etc for a movie
        self.person_set = set()

        # Predefine as -1 to penalize if ratings are not found
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

    # Make it so that people can input any imdb link and then you isolate the title

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

    # Map movie link to Movie objects
    movie_dict = {}

    # Iterate over movies, extract class members
    for movie_link in links_identified:
        try:
            current_page = only_session.get(movie_link, timeout=3, headers=Header_Info)
            current_soup = bs(current_page.content, features="html.parser")    
            
            # Create movie obj
            movie_obj = Movie(movie_link)

            try:
                # Find movie title
                title_obj = current_soup.find("span", class_="sc-afe43def-1 fDTGTb")
                movie_title = title_obj.get_text()
                movie_obj.title = movie_title
            except Exception as e:
                print(f"Movie title error: {e}")

            try:
                # Find meta score
                metascore_obj = current_soup.find("span", class_="score-meta")
                metascore = metascore_obj.get_text()
                movie_obj.metascore = metascore
            except Exception as e:
                print(f"Metascore error: {e}")

            try:
                # Find IMDB rating
                imdb_obj = current_soup.find("span", class_="sc-bde20123-1 iZlgcd")
                imdb_rating = imdb_obj.get_text()
                movie_obj.imdb_rating = imdb_rating
            except Exception as e:
                print(f"IMDB rating error: {e}")

            # Find Genres
            # breakpoint()
            # genre_divs = current_soup.find("div", attrs={'datatest-id':'genres'})
            # for div in genre_divs.find_all("span", class_='ipc-chip__text'):
            #     print(div)

            # Take all links, narrow down to links for "names"
            for link_obj in current_soup.find_all('a'):
                try:
                    link = link_obj.get('href')
                    stripped = url_strip(link)

                    # Check if link format is right before adding
                    if stripped.startswith("/name/"):
                        movie_obj.add_person(f"https://www.imdb.com{isolate_name(stripped)}")
                except Exception as e:
                    print(f"Person error: {e}")
            
            # Add movie obj to list
            print(f"Added {movie_title} to movie list.")
            movie_dict[movie_link] = movie_obj

        except requests.exceptions.RequestException as e:
            print(f"Error Message: {e}")

    # Map titles to scores
    score_dict = {} 

    # Value is movie object
    for value in movie_dict.values():
        # Don't include the originally provided movie
        if value == movie_dict[seedUrl]:
            continue
        else:
            # IMDB/10 + metacritic/100 + jaccard similarity * average length of sets
            set_a = value.person_set
            set_b = movie_dict[seedUrl].person_set
            average_length = (len(set_a) + len(set_b))/2
            jaccard_similarity = len(set_a.intersection(set_b))/len(set_a.union(set_b))
            score = (float(value.imdb_rating)/10) + (float(value.metascore)/10) + (jaccard_similarity * average_length) 
            score_dict[value.title] = score

    # Sort score dict, take top X results
    outputList = []
    for key, value in score_dict.items():
        outputList.append((key, value))
    outputList.sort(key = lambda x: x[1], reverse=True)

    # Writing to output file
    with open('crawler.output', 'w') as output:
        count = 1
        output.write("Results are in descending order, showing the movie title and the associated custom score. \n")
        while count <= desired_results:
            output.write(f"{count}. {outputList[count][0]} : {outputList[count][1]} \n")
            count += 1

if __name__ == '__main__':
    main()
