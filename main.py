#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib import websitepuller
from lib import govzipsandcities
from lib import craigzipsandurls

zip_code_file = ('/home/john/gitrepos/shouldipickitup/data/free-zipcode-database-Primary.no.header.csv')

def main(zip):

    start_lat = '40.6490763'
    start_lng = '-73.9762069'

    start_lat = '29.5964'
    start_lng = '-82.2178'

    ''' Given a zip, find the closest numerial match and return city,state names '''
    try:
        city, state = govzipsandcities.lookup_city_state_given_zip_memcached(zip)
        citytext = f"{city},{state}"
        citytext = citytext.lower() #not needed?
    except ValueError:
        citytext = ""
    except ConnectionRefusedError:
        city, state = govzipsandcities.lookup_city_state_given_zip_file(zip,zip_code_file)
        city, state = city.lower() , state.upper()
        citytext = f"{city},{state}"
        #citytext = citytext.lower()
        print(f"Debug citytext: {citytext}")

    ''' Given a city name, find the closest local Craigslist Url '''
    try:
        craigs_list_url = craigzipsandurls.lookup_craigs_url_memcached(citytext)
        craigs_list_url = craigs_list_url.decode('UTF-8')
    except ValueError:
        craigs_list_url = 'https://sfbay.craigslist.org' #no trailing /
    except ConnectionRefusedError:
        try:
            print('h1')
            web_links = craigzipsandurls.create_craigs_url_dict_from_disk()
            craigs_list_url = craigzipsandurls.lookup_craigs_url_from_dict_file(citytext, web_links)
            print(f"Debug url: {craigs_list_url}")
        except Exception as e:
            print('eeeeeeqq',type(e),e)
        #else:
        #   print(f"Debug: {citytext} is available at {craigs_list_url}")

    ''' Given the the closest local Craigslist url, return the free items '''
    print('h2')
    craigs_local_url   = craigs_list_url + "/d/free-stuff/search/zip"
    print('h3')
    craigs_local_posts = websitepuller.lookup_craigs_posts(craigs_local_url)

    ''' Given the free items, see:                      '''
    ''' 1) How far away?                                '''
    ''' 2) How much on Ebay                             '''
    ''' 3) How much for a Lyft                          '''

    ''' only show me 5 items '''
    all_posts = []
    for each_item in craigs_local_posts[0:3]:
        end_lat,end_lng,miles  = websitepuller.lookup_miles_from_user(each_item,start_lat,start_lng)
        #price                  = websitepuller.lookup_price_on_ebay(each_item)
        price = 5
        #mind,maxd              = websitepuller.lookup_cost_lyft(start_lat,start_lng,end_lat,end_lng)
        mind,maxd = 8, 9
        printable_data         = (f"{each_item.text} is Free on Craigslist in "
            f"{city}, and is selling for {price} on Ebay and is {miles:.2f} miles away"
            f"from you. Using Lyft it will cost between {mind} and {maxd} dollars to"
            f"pick up.\n")
        all_posts.append(printable_data)
        #all_posts_text =  " ".join(str(x) for x in all_posts)
    #return all_posts_text
    return all_posts

if __name__ == "__main__":

    import sys

    try:
        zip = sys.argv[1]
    except IndexError as e:
        print(e,"Did you specify a zip?")
        sys.exit()

    try:
        print (main(zip))
    except Exception as e:
        print(e)
