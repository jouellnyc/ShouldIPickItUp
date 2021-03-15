#!/usr/bin/env python3

""" crawler.py  - Web Crawler

-This script:
    - Takes in a Craigslist URL
    - Crawls the page
    - Prepares a MongoDB insert_one_document
    - Sends data to  MongoDB

-If no data matches or if MongoDB errors, S.F data will be returned
-This script requires the mongodb and websitepuller helper modules.
-This file is mean to be run outside of the Flask Appself.

"""

import os
import sys
import datetime
import logging

import mongodb
import websitepuller
import pickledata


# "crawler.log"
logname = os.path.splitext(os.path.basename(__file__))[0] + ".log"

logging.basicConfig(
    filename=logname,
    level="INFO",
    format="%(levelname)s %(asctime)s %(module)s %(process)d  %(message)s",
)


def format_mongodocs(soup_object, ebay_prices, ebay_links, howmany=12):
    """ Return Formatted Mongdo Doc
    
    Parameters
    ----------
    soup_object
        beautiful soup_object - list of all free items crawled
    howmany
        number of items to return from CL page

    Returns
    -------
    mongo_doc
        dictionary of dictionaries  - mongo_doc object -

    - We use an Embedded Mongo Doc to List Items and URls

     mongo_doc will look like this:
                {
                    "$set":

                    { Items:

                    item1 : each_text1, url1: each_link1,
                    item2 : each_text2, url2: each_link2,
                    item3 : each_text3, url3: each_link3

                    }

                        ... and so on for Urls, Price and EbayLinks
                }
    """
    mongo_filter = {"craigs_url": craigs_list_url}
    mongo_doc = {
        "$set": {
            "Items": {},
            "Urls": {},
            "Prices": {},
            "EbayLinks": {},
            "DateCrawled": "",
        }
    }

    for num, each_item in enumerate(soup_object[0:howmany], start=1):
        each_link = each_item.attrs["href"]
        each_text = each_item.text
        item = f"Item{num}"
        url = f"Url{num}"
        mongo_doc["$set"]["Items"][item] = each_text
        mongo_doc["$set"]["Urls"][url] = each_link

    for num, price in enumerate(ebay_prices[0:howmany], start=1):
        price_num = f"Price{num}"
        mongo_doc["$set"]["Prices"][price_num] = price

    for num, link in enumerate(ebay_links[0:howmany], start=1):
        link_num = f"EbayLink{num}"
        mongo_doc["$set"]["EbayLinks"][link_num] = link

    mongo_doc["$set"]["DateCrawled"] = datetime.datetime.now()

    return mongo_doc


if __name__ == "__main__":

    try:

        verbose = True
        timeout = 45
        howmany = 15 
        craigs_list_url = sys.argv[1]
        noindex = sys.argv[2]


        msg = f"==== Connecting to {craigs_list_url} ===="
        print(msg)
        logging.info(msg)
        craig_raw_posts = websitepuller.get_craigs_list_free_posts(craigs_list_url)
        for x in craig_raw_posts:
            logging.info(f"Picked up {x.get('href')} - {x.getText()}")


        msg = f"==== Connecting to Ebay - {timeout}s timeout, {howmany} items ===="
        print(msg)
        logging.info(msg)
        craig_posts_with_data, ebay_prices, ebay_links = websitepuller.get_ebay_data(
            craig_raw_posts, random="yes", howmany=howmany, timeout=timeout
        )
        logging.info("Ending Crawl of {craigs_list_url}")


        print("==== Formatting Docs  ====")
        mongo_doc = format_mongodocs(
            craig_posts_with_data, ebay_prices, ebay_links, howmany=howmany
        )
        mongo_filter = {"craigs_url": craigs_list_url}
        if verbose:
            print(mongo_doc)


    except IndexError:
        print("URL or noidex?")
        sys.exit()

    except (ValueError, NameError) as e:
        logging.exception(f"Data Issue: {e}")

    except Exception as e:
        logging.exception(f"Unhandled Crawl error: {e}")

    else:
        if noindex == "noindex":
            print("Pickling...")
            pickledata.save(mongo_doc)
        else:
            print("Sending to Mongo")
            try:
                mongo_cli = mongodb.MongoCli()
                if mongo_cli.dbh:
                    print(mongo_filter, mongo_doc)
                    mongo_cli.update_one_document(mongo_filter, mongo_doc)
                else:
                    msg='Cannot connect to Mongo'
                    logging.exception(msg)
                    print(msg)
                    sys.exit(1)
            except Exception as e:
                logging.exception(f"Unhandled Database related error: {e}")
            else:
                print("Sent to Mongo Success")
