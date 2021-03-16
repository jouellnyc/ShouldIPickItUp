#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

main.py - interface into flask and mongodb.
- This script takes in a zipcode code from Flask/app.py or via cmd line, and then
determines the right Craiglist URL by qurying 'Zips' or 'AltZips' in MongoDB.
It then returns the free items (see below) associated with that MongoDB doc.

- If there is no data for the zipcode entered, S.F data will be returned
- If MongoDB is down S.F data will be returned (if data was crawled and loaded)

-This script requires the mongodb helper module.

-This file can also be imported as a module and contains the following
functions:

    * main - the main function of the script

TBD: If MondoDB is down don't load a file every time ...

"""

import logging

# logger = logging.getLogger(__name__)

import pymongo
from pymongo.errors import ConnectionFailure

from lib import mongodb
from lib import pickledata


def main(zipcode):
    """Send data to flask template for display after querying MongoDB.

    Parameters
    ----------
    zipcode : str
        zipcode code the user entered - inbound from Flask or from cmd line.

    Returns
    -------
    all_posts
        A [list] of all the local posts in the free sections
    all_links
        A [list] of all the local posts in the free sections
    city
        [str] - the city associated with the zipcode (for display only)
    state
        [str] - the state associated with the zipcode (for display only)

    start_lat
    start_lng    to be used to calculate distance (disabled for now)

    """
    start_lat = "40.6490763"
    start_lng = "-73.9762069"

    start_lat = "29.5964"
    start_lng = "-82.2178"

    """ Defaults - Worst Case scenario """
    fall_back_url = "https://sfbay.craigslist.org/d/free-stuff/search/zipcode"
    all_posts = ["Items Error"] * 12
    all_links = [fall_back_url] * 12
    all_cust = list(zip(all_links, all_posts))
    city, state = (
        f"Sorry didn't find data for {zipcode} " f"here's items for San Francisco",
        "CA",
    )
    try:

        """ Given a zipcode, find the Craigslist Url """
        mongocli = mongodb.MongoCli()
        all_data = mongocli.lookup_all_data_given_zip(zipcode)
        city = all_data.city.capitalize()
        state = all_data.state.capitalize()
        all_posts = list(all_data.Items.values())
        all_links = list(all_data.Urls.values())
        all_prices = list(all_data.Prices.values())
        all_eblnks = list(all_data.EBlinks.values())
        all_cust = list(zip(all_eblnks, all_prices))

    except (ValueError, KeyError) as e:

        msg = f"Going to retrieve pickle data"
        all_posts, all_links = fallback_to_pickle()
        logger.error(f"{msg} => {str(e)}")

    except ConnectionFailure as e:

        msg = "MongoDB Connection Errors - DB down? "
        all_posts, all_links = fallback_to_pickle()
        logger.error(f"{msg} => {str(e)}")

    except Exception as e:

        msg = "Unexpected Error=> "
        logger.error(f"{msg} => {str(e)}")

    else:

        print("Match:", craigs_list_url, city, state, items)

    finally:
        return all_posts, all_links, all_cust, city, state

        """ Given the free items, see:                      """
        """ 1) How far away?                                """
        """ 2) How much on Ebay                             """
        """ 3) How much for a Lyft                          """


def fallback_to_pickle():
    """ Return SF data from local if Mongdb is down/server Timeout.
    Parameters
    ----------
    none

    Returns
    -------
    all_posts
        A [list] of all the local posts in the free sections
    all_links
        A [list] of all the local posts in the free sections
    """
    try:
        pickled = pickledata.loadit(file="data/sf.pickle")
        all_posts = list(pickled["$set"]["Items"].values())
        all_links = list(pickled["$set"]["Urls"].values())
        return all_posts, all_links
    except (IOError, KeyError, TypeError) as e:
        msg = "Even the file is erroring!: "
        logger.error(f"{msg} => {str(e)}")
        # Sms/page out


if __name__ == "__main__":

    import sys

    try:
        zipcode = sys.argv[1]
    except IndexError as err:
        msg = "Did you specify a zipcode or a url?"
        print(msg)
        sys.exit()
    else:
        print("Main: ", main(zipcode))
