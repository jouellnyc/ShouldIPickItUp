import datetime

def format_mongodocs(mongo_filter, craig_posts_with_data, ebay_prices, ebay_links, howmany=12):
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
    mongo_doc = {
        "$set": {
            "Items": {},
            "Urls": {},
            "Prices": {},
            "EbayLinks": {},
            "DateCrawled": "",
        }
    }

    for num, each_item in enumerate(craig_posts_with_data[0:howmany], start=1):
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

