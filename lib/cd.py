#!/home/john/anaconda3/bin/python3
import mongodb
mg = mongodb.MongoCli()
for x in mg.dbh.find({'DateCrawled' : {"$exists": True} }): 
    print (x['DateCrawled'], x['craigs_url'])
