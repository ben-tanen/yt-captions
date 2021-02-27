# -*- coding: utf-8 -*-

import os
import youtube_dl

if os.getcwd()[-11:] != "yt-captions":
    os.chdir("/Users/ben-tanen/Desktop/Projects/yt-captions")

opts = {
    "skip_download": True, 
    "writesubtitles": True,
    "writeautomaticsub": False,
    "subtitleslangs": ["en", "en-US"],
    "geo_bypass": "US",
    "outtmpl": os.getcwd() + "/captions/%(id)s.user.%(ext)s"
}

opts_auto = dict(opts)
opts_auto.update({"writeautomaticsub": True,
                  "outtmpl": os.getcwd() + "/data/captions/%(id)s.auto.%(ext)s"})

yt = youtube_dl.YoutubeDL(opts)
yt_auto = youtube_dl.YoutubeDL(opts_auto)

vid_ids = ["hqvOcr0uu9o", "2l14XtJwVUc", "4b33NTAuF5E"]
vid_ids = ["ymyY7jez0rM"]

youtube_dl.YoutubeDL({"listsubtitles": True, "print_json": True}).download(["https://www.youtube.com/watch?v=ymyY7jez0rM"])

yt.download(["https://www.youtube.com/watch?v=%s" % vid for vid in vid_ids])
yt_auto.download(["https://www.youtube.com/watch?v=%s" % vid for vid in vid_ids])
