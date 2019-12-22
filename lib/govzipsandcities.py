#!/home/john/anaconda3/bin/python3.7

''' Build and load zip code data into a file or memcached and '''
''' make available functions to return that data              '''

import os
import re
import csv
import sys

from pymemcache.client import base

URL = 'http://federalgovernmentzipcodes.us/download.html' # not used
my_file_name = os.path.basename(__file__)
zip_code_file = ('/home/john/gitrepos/shouldipickitup/data/free-zipcode-database-Primary.no.header.csv')

def create_zips_city_state_dict_from_file(zip_code_file):
    ''' Return a dictionary with zip : (city,state) tuples  '''
    ''' give the file at URL                                '''

    with open(zip_code_file) as csv_fh:
            myzips = {}
            csv_reader = csv.reader(csv_fh, delimiter=',')

            for row in csv_reader:
                zip   = row[0]
                city  = row[2]
                state = row[3]
                myzips[zip] = (city,state)

    return myzips

def load_zips_to_memcached(zipcode_dict):
    ''' write all the key/values to memcached '''
    client = base.Client(('localhost', 11211))
    for zip,(city,state) in zipcode_dict.items():
        client.set(zip,(city,state))

def lookup_city_state_given_zip_file(zip,zip_code_file):
    ''' Given a zipcode;  return closest city,state zipcode dictionary file '''
    myzips  = create_zips_city_state_dict_from_file(zip_code_file)
    closest = myzips[min(myzips.keys(), key=lambda k: abs(int(k)-int(zip)))]
    city, state = closest
    return (city,state)

def lookup_city_state_given_zip_memcached(zip):
    ''' Given a zipcode and the zipcode dictionary return closest city,state '''
    ''' as a tuple. If no hit, find the closest and cache that in memcached  '''
    #if memcached is down ConnectionRefusedError is returned
    client      =  base.Client(('localhost', 11211))
    data        = client.get(zip)

    if data is None:
        raise ValueError('No data')
    else:
        city, state = data.decode("utf-8").split(',')
        patt  = re.compile('\w+')
        city  = patt.search(city).group()
        state = patt.search(state).group()
        city, state = city.lower(),state.lower()
        return (city,state)

if __name__ == "__main__":

    import sys
    import app_logger

    try:
        zip = sys.argv[1]
        myzips = create_zips_city_state_dict_from_file(zip_code_file)
        #print(myzips)
    except OSError as e:
        print("OSError",e)
    except IndexError as e:
        print("Did you specify a zip?")
    else:
        try:
            load_zips_to_memcached(myzips)
            city,state = lookup_city_state_given_zip_memcached(zip)
            print(city,state)
        except Exception as e:
            #print("Memcached seems down; going to file:",e)
            try:
                city, state = lookup_city_state_given_zip_file(zip_code_file)
                city, state = city.lower(),state.lower()
                print(city,state)
            except OSError as e:
                print("OSError",e)
else:
    from . import app_logger
