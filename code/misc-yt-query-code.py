# -*- coding: utf-8 -*-

import json, math
from apiclient.discovery import build
import pandas as pd

# import api key and init youtube instance
api_keys = json.load(open("data/setup/api-keys.json"))
youtube = build('youtube', 'v3', developerKey = api_keys["yt-data-api-key"])

# loop through YT searches to get top channels by viewCount
channels = [ ]
nextPageToken = None
for x in range(0, 10):
    # search for channels by viewCount
    # using nextPageToken from prev searches
    data = youtube.search().list(
        pageToken = nextPageToken,
        part = "snippet",
        type = "channel",
        maxResults = 50,
        order = "viewCount"
    ).execute()
    
    # append channel data to running list
    channels += [{'channelTitle': e['snippet']['channelTitle'],
                  'channelId': e['id']['channelId']} for e in data['items']]
    
    # get nextPage token (for future searches)
    nextPageToken = data['nextPageToken']
    print(nextPageToken)
    
# convert channel search data into data frame and see # of results
df = pd.DataFrame(channels)
df.drop_duplicates().count()

# loop through channel ids and get statistics on channel (views, subs, etc.)
channel_data = [ ]
for x in range(0, math.ceil(df['channelId'].count() / 50)):    
    # get snippet + stats from channel ids
    # parse out 50 ids per iter
    data = youtube.channels().list(
        part = "snippet,contentDetails,statistics",
        id = ",".join(list(df['channelId'][(x * 50):(x * 50 + 50)])),
        maxResults = 50
    ).execute()
    
    # append channel stats data
    channel_data += [{'channelId': e['id'],
                      'subscriberCount': int(e['statistics']['subscriberCount']),
                      'viewCount': int(e['statistics']['viewCount']),
                      'videoCount': int(e['statistics']['videoCount'])} for e in data['items']]
    
# convert channel stats data into data frame and merge onto channel search data
df2 = pd.DataFrame(channel_data)
df3 = df.merge(df2, how = 'left', on = 'channelId')

d = youtube.channels().list(
    part = "snippet,contentDetails,statistics,localizations",
    forUsername = "blackboxfilmcompany",
    maxResults = 10
).execute()

# get caption information for video
d = youtube.captions().list(
    part = "id,snippet",
    videoId = "erQ_9yEz0ls"
).execute()

# parse out type and language for caption tracks
[{'lang': cap['snippet']['language'], 'type': cap['snippet']['trackKind']} for cap in d['items']]


    
    

