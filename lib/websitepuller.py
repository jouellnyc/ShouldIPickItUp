#!/usr/bin/env python3

""" websitepuller.py - pull data for *each* item  - Ebay, Lyft or Craiglist

- This script is a library for lookup on Ebay, CraigList and Lyft
- This script requires the requests BeautifulSoup module and geopy
- This file is meant to be imported as a module.
"""

import re
import json
import logging
import time
from random import randrange

import requests.exceptions
from bs4 import BeautifulSoup
from geopy.distance import geodesic

try:
    from lib import requestwrap  # if called from ..main()
except ModuleNotFoundError:
    import requestwrap  # if called from .


class HTTPError(Exception):
    pass



mapsre = re.compile("https://www.google.com/maps/preview/")


def lookup_miles_from_user(each_item, start_lat, start_lng):
    """
    Parameters
    ----------
    each_item : BeautifulSoup object
        Pointer to each free item

    Returns
    -------
    end_lat - string
        Final latitude - where the free item is
    end_lng
        Final longitude - - where the free item is
    miles - int
        Distance from user

    Exceptions
        AttributeError - a post without any text
    """
    item_url = each_item.attrs["href"]
    craigs_resp = requestwrap.err_web(item_url)
    craigs_soup = BeautifulSoup(craigs_resp.text, "html.parser")
    googurl = craigs_soup.find("a", href=mapsre)

    try:
        end_lat, end_lng, _ = (
            googurl.attrs["href"].split("@")[1].split("z")[0].split(",")
        )
        miles = geodesic((start_lat, start_lng), (end_lat, end_lng)).mi
        return end_lat, end_lng, miles
    except AttributeError:
        print(f"{each_item.text} was likely deleted")
        raise


def lookup_cost_lyft(start_lat, start_lng, end_lat, end_lng):
    """
    Parameters
    ----------
    start_lat, start_lng, end_lat, end_lng - strings
        - Start latitude and longitude from user to item

    Returns
    -------
    mind, maxd - strings
        - minimum and maximum Lyft cost
    """
    lyft_url = "http://www.lyft.com"
    lyft_path = f"/api/costs?start_lat={start_lat}&start_lng={start_lng}&end_lat={end_lat}&end_lng={end_lng}"
    lyft_costurl = lyft_url + lyft_path
    lyft_resp = requestwrap.err_web(lyft_costurl)
    fares = json.loads(lyft_resp.content)
    min = fares["cost_estimates"][0]["estimated_cost_cents_min"]
    max = fares["cost_estimates"][0]["estimated_cost_cents_max"]
    mind = min / 100
    maxd = max / 100
    return mind, maxd


def lookup_city_from_cl_url(craiglisturl):
    craigs_first_free = requestwrap.err_web(craiglisturl)
    craigs_first_free_soup = BeautifulSoup(craigs_first_free.text, "html.parser")
    try:
        metacity = (
            craigs_first_free_soup.find("meta", attrs={"name": "geo.placename"})
            .get("content")
            .lower()
        )
        metacity = "".join(metacity.split())
        _, metastate = (
            craigs_first_free_soup.find("meta", attrs={"name": "geo.region"})
            .get("content")
            .split("-")
        )
    except AttributeError as e:
        print(e)
        return None
    else:
        return metacity, metastate


def get_city_from_first_free_cl_item(craigs_list_url):
    first_item_soup = get_craigs_list_free_posts(craigs_list_url)[0]
    url = first_item_soup.attrs["href"]
    city = lookup_city_from_cl_url(url)
    if city is not None:
        return city
    else:
        return None


def get_craigs_list_free_posts(craigs_list_url):
    """ Connect to Craigslist by appending the free URL params.
        Get the Free posts and return them.
        
    Parameters
    ----------
    craigs_list_url
        str - local Craigs List Url

    Returns
    -------
    craigs_free_posts
        beautiful soup_object - list of all free items
        
        craig_posts_with_data, ebay_prices, ebay_links
        
    """

    if "newyork" in craigs_list_url:

        try:
            proto, _, url, suffix, *other = craigs_list_url.split("/")
        except Exception as e:
            print("New York URL unpacking error?", str(e))
            raise
        else:
            craigs_free_url = (
                f"{proto}//{url}/d/free-stuff/search/{suffix}/zip"  # https://
            )

    else:
        craigs_free_url = craigs_list_url + "/d/free-stuff/search/zip"

    logging.info(f"Scraping {craigs_free_url}")
    craigs_response = requestwrap.err_web(craigs_free_url)
    craigs_soup = BeautifulSoup(craigs_response.text, "html.parser")
    craigs_free_posts = craigs_soup.find_all("a", class_="result-title hdrlnk")
    return craigs_free_posts


def get_ebay_data(craig_raw_posts, random="yes", howmany=12, timeout=30):

    """
    Parameters
    ----------
    craig_raw_posts: BeautifulSoup objects collected from free posts
    random: string - whether to randomize sleeping crawling Ebay
    howmany: int - how many items with prices to collect
    timeout: int - Ebay Crawl Timout
        
    Returns
    -------
    craig_posts_with_data - list of items with prices scraped from Ebay
    ebay_prices - list of those prices
    ebay_links  - list of those links
    """

    if random == "yes":
        sleep = randrange(15, 45)
    else:
        sleep = 0
    ebay_prices = []
    ebay_links = []
    craig_posts_with_data=[]
    
    count=0
    
    for num, each_post in enumerate(craig_raw_posts):
           
            logging.info(f"Count of items with price and link: {count}")
        
            try:
                price, eb_link = lookup_price_on_ebay(num, each_post,timeout=timeout)
            except ValueError:
                continue
            except HTTPError:
                continue
            else:
                try:
                    price = price.replace("$", "")
                    float(price)
                except ValueError:
                    continue
                else:
                    ebay_prices.append(price)
                    ebay_links.append(eb_link)
                    craig_posts_with_data.append(each_post)
                    count+=1
                    if count == howmany:
                        logging.info(f"{howmany} items achieved Stopping Crawl")
                        break
            logging.info(f"Sleeping {sleep} seconds")        
            time.sleep(sleep)
            
    return craig_posts_with_data, ebay_prices, ebay_links

def lookup_price_on_ebay(num, each_post, timeout=30):
    """
    Parameters
    ----------
    each_post : BeautifulSoup object - bs4.element.Tag
        Pointer to each free item

    num: Index from enumerate()
    
    Returns
    -------
    price - string
        Price as per Ebay
    Exceptions
        ValueError- a post without price and link info
    """

    try:
        ebay_url = "https://www.ebay.com/sch/i.html?_from=R40&_trksid=m570.l1313&_nkw="
        ebay_path = (
            f"{each_post.text}&_sacat=0&LH_TitleDesc=0&_osacat=0&_odkw={each_post.text}"
        )
        ebay_query_url = ebay_url + ebay_path
        logging.info(f"{num} - Querying {ebay_query_url}")
        ebay_resp = requestwrap.err_web(ebay_query_url, timeout=timeout)
        ebay_soup = BeautifulSoup(ebay_resp.text, "html.parser")
        ebay_item_text = ebay_soup.find("h3", {"class": "s-item__title"}).get_text(separator=" ")
    except AttributeError:
        msg = f"{num} - No match on Ebay"
        logging.warning(f"{msg} for {each_post.text}")
        raise ValueError("{msg}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{num} - {e} - {each_post.text}")
        raise HTTPError
    except Exception as e:
        msg = "Unhandled"
        logging.error(f"{msg} - {num} - {e} - {each_post.text}")
        raise ValueError("{msg}")
    else:
        logging.info(f"{num} - Crawled Ebay OK - search returned: {ebay_item_text}")
        # Keep only items with price and links
        try:
            price = ebay_soup.find("span", {"class": "s-item__price"}).get_text()
        except AttributeError:
            msg = f"{num} - No price on Ebay"
            logging.warning(f"{msg}  for {ebay_item_text}")
            raise ValueError("{msg}")
        else:
            try:
                eb_link = ebay_soup.find("a", {"class": "s-item__link"})
                eb_link = eb_link.attrs["href"]
                eb_link = eb_link.partition("?")[0]
            except AttributeError:
                msg = "Price, but no link on on Ebay?"
                logging.warning(f"{msg} for  {ebay_item_text}")
                raise ValueError("{msg}")
            else:
                logging.info(f"{num} - Retrieved price of {price} at {eb_link}")
            return (price, eb_link)


