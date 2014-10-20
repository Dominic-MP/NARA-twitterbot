#!/usr/bin/env python
# -*- coding: utf-8 -*-

###### INSTRUCTIONS ######
#
#This script relies on tweepy (https://github.com/tweepy/tweepy), which can be installed with easy_install or pip.
#
# "settings" is imported from a settings.py file I created in the same directory, so that the script can be shared without revealing credentials for my Twitter account. The settings file looks like (with credentials filled in):
## CONSUMER_KEY = 'XXX'
## CONSUMER_SECRET = 'XXX'
## ACCESS_KEY = 'XXX'
## ACCESS_SECRET = 'XXX'
#
# To run the script, just use "python nara-twitterbot.py". This will post the tweets using search results for random NARA photographic item records on the current date in history. You can also use an optional argument to limit searches to a given keyword. For example, use the command "python nara-twitterbot.py eisenhower" if you want the bot to only tweet about records with the keyword "Eisenhower" (for an anniversary, for example).

import settings, tweepy, requests, json, datetime, random, time, sys, argparse
from datetime import date

# This is where the script logs into the Twitter API using your application's settings.

auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
auth.set_access_token(settings.ACCESS_KEY, settings.ACCESS_SECRET)
api = tweepy.API(auth)

# Here we read the optional argument given. If it's not given, the variable "q" is set to null, but if it is present, we use the argument to generate the keyword parameter for the OPA API call later on.

q = ""
parser = argparse.ArgumentParser()
parser.add_argument('--keyword', dest='keyword', metavar='KEYWORD',
                    action='store')
parser.add_argument('--upperyear', dest='upperyear', metavar='UPPERYEAR',
                    action='store')
parser.add_argument('--loweryear', dest='loweryear', metavar='LOWERYEAR',
                    action='store')
args = parser.parse_args()
                    
if args.keyword :
	q = "&q=" + args.keyword	

# This part takes today's date and uses it to generate the OPA API query based on the month and day. This first API query is just to find out the number of results in the result set, and the rest is not used. We are searching for items with the record type of "Photographs and other Graphic Materials (NAID 10035674), produced on the current day and month. Then we parse the JSON and extract the total number of results for the query.

d = date.today()

rowsurl = 'https://uat.research.archives.gov/api/v1/?resultTypes=item&rows=1&description.item.generalRecordsTypeArray.generalRecordsType.naId=10035674&description.item.productionDateArray.proposableQualifiableDate.month=' + str(d.month) + '&description.item.productionDateArray.proposableQualifiableDate.day=' + str(d.day) + q
rowsparse = json.loads(requests.get(rowsurl).text)
rows = rowsparse['opaResponse']['results']['total'] - 1

# The hackish way to make this script continue infinitely.

x = 0
while x == 0 :

# This is where we actually construct the API query that we will use to extract the NAID and title for our tweet. This is the exact same query as above, using today's date, except that we are using the API's "offset" parameter to specify a particular record. We are using the total number of results which we determined above (the variable "rows") so that each time the script defines "geturl", it does it by picking a random result inside the bounds of the result set total, which will change each day. This is why we subtracted 1 from the results set total to define rows, since the API numbers starting from 0, and it will thrown an error if offset=rows.

	geturl = 'https://uat.research.archives.gov/api/v1/?resultTypes=item&rows=1&description.item.generalRecordsTypeArray.generalRecordsType.naId=10035674&description.item.productionDateArray.proposableQualifiableDate.month=' + str(d.month) + '&description.item.productionDateArray.proposableQualifiableDate.day=' + str(d.day) + '&offset=' + str(random.randint(0,rows)) + q

# Get the API query and parse the JSON.

	tweet = requests.get(geturl)
	parsed = json.loads(tweet.text)

	if int(args.loweryear) < int(parsed['opaResponse']['results']['result'][0]['description']['item']['productionDateArray']['proposableQualifiableDate']['year']) < int(args.upperyear) :

# This prints the NAID, image URL, and tweet text just so we can watch the bot in the command line as it works.
		
		print args.loweryear + args.upperyear
		print parsed['opaResponse']['results']['result'][0]['naId']
		print parsed['opaResponse']['results']['result'][0]['objects']['object']['file']['@url']
		print "Here's a NARA record for today's date (" + str(d.month) + "/" + str(d.day) + ") in " + parsed['opaResponse']['results']['result'][0]['description']['item']['productionDateArray']['proposableQualifiableDate']['year'] + ": \"" +  parsed['opaResponse']['results']['result'][0]['description']['item']['title'] [0:57] + "...\" uat.research.archives.gov/id/" + parsed['opaResponse']['results']['result'][0]['naId']

# Here's the actual posting of the tweet, using tweepy's syntax. The title field is automatically truncated at 54 characters, so that the tweets are all 140 characters exactly, or less. Right now, this adds an ellipsis automatically, even if truncation wasn't necessary. OPA URLs are created programmatically using the NAID.

		api.update_status("Here's a NARA record for today's date (" + str(d.month) + "/" + str(d.day) + ") in " + parsed['opaResponse']['results']['result'][0]['description']['item']['productionDateArray']['proposableQualifiableDate']['year'] + ": \"" + parsed['opaResponse']['results']['result'][0]['description']['item']['title'] [0:57] + "...\" uat.research.archives.gov/id/" + parsed['opaResponse']['results']['result'][0]['naId'])
	
# This tells the script to run the bit inside the while loop again, randomly generating a new tweet every 10 minutes. 

		time.sleep(600)
	
	else :
		print "Found NAID " + parsed['opaResponse']['results']['result'][0]['naId'] + " from " + parsed['opaResponse']['results']['result'][0]['description']['item']['productionDateArray']['proposableQualifiableDate']['year'] + ". Repeating..."