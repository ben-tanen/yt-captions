# -*- coding: utf-8 -*-

import json
from apiclient.discovery import build
import pandas as pd
from datetime import datetime

# import api key and init youtube instance
api_keys = json.load(open("data/api-keys.json"))
youtube = build('youtube', 'v3', developerKey = api_keys["yt-data-api-key"])

# loop through YT trending videos
trendingVids = [ ]
nextPageToken = None
for x in range(0, 3):
    # get top trending videos
    # using nextPageToken from prev searches
    data = youtube.videos().list(
        pageToken = nextPageToken,
        part = "snippet,statistics",
        chart = "mostPopular",
        maxResults = 50
    ).execute()
    
    # append channel data to running list
    trendingVids += [{
        'channelTitle': e['snippet']['channelTitle'],
        'channelId': e['snippet']['channelId'],
        'videoTitle': e['snippet']['title'],
        'videoTitleLoc': e['snippet']['localized']['title'],
        'videoId': e['id'],
        'videoTags': '|'.join(e['snippet']['tags']),
        'views': int(e['statistics']['viewCount']),
        'queryTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    } for e in data['items']]
                     
    # get nextPage token (for future searches)
    if "nextPageToken" in data:
        nextPageToken = data['nextPageToken']
        
# assign trending rank to videos
for ix in range(0, len(trendingVids)):
    trendingVids[ix]['trendingRank'] = ix + 1

# get caption information for trending videos
captions = [ ]
for vid in trendingVids:
    data = youtube.captions().list(
        part = "id,snippet",
        videoId = vid['videoId']
    ).execute()
    
    captions += [{
        'videoId': vid['videoId'],
        'captionLang': e['snippet']['language'],
        'captionType': e['snippet']['trackKind']
    } for e in data['items']]
    
# convert to data frames and merge together
vid_df = pd.DataFrame(trendingVids)
cap_df = pd.DataFrame(captions)

combine_df = vid_df.merge(cap_df, how = 'left', on = 'videoId')

# save to excel
combine_df.to_csv("data/%s_trending-vid-captions.xlsx" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

