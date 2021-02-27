# -*- coding: utf-8 -*-

import os, sys, json, math
from apiclient.discovery import build
import pandas as pd
from datetime import datetime

os.chdir("/Users/ben-tanen/Desktop/Projects/yt-captions")

# import api key and init youtube instance
api_keys = json.load(open("data/setup/api-keys.json"))
youtube = build('youtube', 'v3', developerKey = api_keys["yt-data-api-key"])

######################
## HELPER FUNCTIONS ##
######################

# get n top trending videos from particular category (0 = no category)
def getTrendingVideos(n = 50, category = 0):
    vids = [ ]
    nextPageToken = None
    
    # query 1 - 4 times (depending on how many videos desired)
    # max results from YT is 200 with 50 per time
    for ix in range(0, math.ceil(min(max(n, 50), 200) / 50)):
        data = youtube.videos().list(
            pageToken = nextPageToken,
            part = "snippet,statistics,topicDetails",
            chart = "mostPopular",
            regionCode = 'us',
            videoCategoryId = category,
            maxResults = min(n - len(vids), 50)
        ).execute()
        
        vids += [{
            'channelTitle': e['snippet']['channelTitle'],
            'channelId': e['snippet']['channelId'],
            'videoTitle': e['snippet']['title'],
            'videoTitleLoc': e['snippet']['localized']['title'],
            'videoId': e['id'],
            'videoSearchCategoryId': str(category),
            'videoCategoryId': e['snippet']['categoryId'],
            'videoViews': int(e['statistics']['viewCount']) if 'viewCount' in e['statistics'] else None,
            'videoQueryTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        } for e in data['items']]
        
        # if no results or end of results, stop looping
        if len(data['items']) == 0 or "nextPageToken" not in data:
            break
        else:
            nextPageToken = data['nextPageToken']
            
    # assign trending rank to videos
    for ix in range(0, len(vids)):
        vids[ix]['videoTrendingRank'] = ix + 1
        
    return(vids)

# get captions for given videos
def getCaptions(videos = [ ]):
    captions = [ ]
    
    for vid in videos:
        data = youtube.captions().list(
            part = "id,snippet",
            videoId = vid['videoId']
        ).execute()
        
        captions += [{
            'videoId': vid['videoId'],
            'captionLang': e['snippet']['language'],
            'captionType': e['snippet']['trackKind']
        } for e in data['items']]
        
    return(captions)

##################################
## QUERY TOP VIDEOS             ##
## THEN CAPTION + CATEGORY INFO ##
##################################

# check if file already exists for today
# if it does, quit
if len([f for f in os.listdir("data") if ".csv" in f and datetime.now().strftime("%Y-%m-%d") in f]):
    print("%s: data already exists for the day" % (datetime.now().strftime("%Y-%m-%d %I:%M %p")))
    sys.exit()

# query top trending videos
try:
    trendingVids = getTrendingVideos(n = 150)
except:
    print("%s: query failed [likely quota issue]" % (datetime.now().strftime("%Y-%m-%d %I:%M %p")))
    sys.exit()
vid_df = pd.DataFrame(trendingVids)

# get caption information for trending videos
captions = getCaptions(videos = trendingVids)
cap_df = pd.DataFrame(captions)

# get video cateogries
cat_data = youtube.videoCategories().list(part = 'snippet', regionCode = 'us').execute()
cat_df = pd.DataFrame([{
    'id': e['id'],
    'videoCategory': e['snippet']['title'],
    'assignable': e['snippet']['assignable']
    } for e in cat_data['items']])

# merge data together
all_df = vid_df.merge(cap_df, how = 'left', on = 'videoId').merge(cat_df, how = 'left', left_on = 'videoCategoryId', right_on = 'id')

# save to excel
all_df.to_csv("data/%s_trending-vid-captions.csv" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), index = False)

print("%s: saved results for day (%d videos)" % (datetime.now().strftime("%Y-%m-%d %I:%M %p"), len(trendingVids)))
