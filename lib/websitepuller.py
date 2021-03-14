#!/usr/bin/env python3

""" websitepuller.py - pull data for *each* item  - Ebay, Lyft or Craiglist

- This script is a library for lookup on Ebay, CraigList and Lyft
- This script requires the requests BeautifulSoup module and geopy
- This file is meant to be imported as a module.
"""

import re
import json
import logging

import requests.exceptions
from bs4 import BeautifulSoup
from geopy.distance import geodesic

try:
    from lib import requestwrap  # if called from ..main()
except ModuleNotFoundError:
    import requestwrap  # if called from .


class HTTPError(Exception):
    pass


def lookup_craigs_posts(craigs_list_url):
    """
    Parameters
    ----------
    craigs_list_url : str
        The 'local' Craig list url.

    Returns
    -------
    craigs_posts : list
        A list of all the BeautifulSoup objects containing free items
    """
    logging.info(f"Scraping {craigs_list_url}")
    craigs_response = requestwrap.err_web(craigs_list_url)
    craigs_soup = BeautifulSoup(craigs_response.text, "html.parser")
    craigs_posts = craigs_soup.find_all("a", class_="result-title hdrlnk")
    return craigs_posts


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


def lookup_price_on_ebay(each_item, timeout=30):
    """
    Parameters
    ----------
    each_item : BeautifulSoup object - bs4.element.Tag
        Pointer to each free item

    Returns
    -------
    price - string
        Price as per Ebay
    Exceptions
        AttributeError - a post without any price info
    """

    try:
        ebay_url = "https://www.ebay.com/sch/i.html?_from=R40&_trksid=m570.l1313&_nkw="
        ebay_path = (
            f"{each_item.text}&_sacat=0&LH_TitleDesc=0&_osacat=0&_odkw={each_item.text}"
        )
        ebay_query_url = ebay_url + ebay_path
        ebay_resp = requestwrap.err_web(ebay_query_url, timeout=timeout)
        ebay_soup = BeautifulSoup(ebay_resp.text, "html.parser")
        item = ebay_soup.find("h3", {"class": "s-item__title"}).get_text(separator=" ")
    except AttributeError:
        msg = "No match on Ebay"
        logging.warning(f"{msg} - {each_item.text}")
        raise ValueError("{msg}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{e} - {each_item.text}")
        raise HTTPError
    except Exception as e:
        msg = "Unhandled"
        logging.error(f"{msg} - {e} - {each_item.text}")
        raise ValueError("{msg}")
    else:
        logging.info(f"Crawled Ebay OK - {item}")
        # Keep only items with price and links
        try:
            price = ebay_soup.find("span", {"class": "s-item__price"}).get_text()
        except AttributeError:
            msg = "No price on Ebay"
            logging.warning(f"{msg} - {each_item.text}")
            raise ValueError("{msg}")
        else:
            try:
                link = ebay_soup.find("a", {"class": "s-item__link"})
                link = link.attrs["href"]
                link = link.partition("?")[0]
            except AttributeError:
                msg = "Price, but no link on on Ebay?"
                logging.warning(f"{msg} - {each_item.text}")
                raise ValueError("{msg}")
            return (price, link)


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
