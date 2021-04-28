#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, re, traceback
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

#=========================#
# DEFINE HELPER FUNCTIONS #
#=========================#

def parse_argv():
    pattern = "--([A-z0-9]+)=(([A-z0-9]|\.|_|-|/)+)"
    if len(sys.argv) > 1:
        parsed_args_list = [{"key": re.match(pattern, arg)[1],
                             "value": re.match(pattern, arg)[2]} for arg in sys.argv[1:]]
        parsed_args = {obj["key"]: obj["value"] for obj in parsed_args_list}
        return parsed_args
    else:
        return {}

def toggle_cc_option():
    cc_btn = driver.find_element_by_xpath("//button[contains(@class, 'ytp-subtitles-button')]")
    cc_btn.click()
    
def toggle_settings_menu():
    settings_btn = driver.find_element_by_xpath("//button[contains(@class, 'ytp-settings-button')]")
    settings_btn.click()

def open_cc_options_list():
    toggle_settings_menu()
    time.sleep(0.5)
    settings_menu = driver.find_elements_by_xpath(("//div[contains(@class, 'ytp-panel-menu')]/div[contains(@class, 'ytp-menuitem')]"))
    settings_menu_labels = [option.find_element_by_xpath("div[contains(@class, 'ytp-menuitem-label')]").get_attribute("innerText") 
                            for option in settings_menu]
    settings_menu_cc_ix = ["ubtitles" in label for label in settings_menu_labels].index(True)
    settings_menu_cc = settings_menu[settings_menu_cc_ix]
    settings_menu_cc.click()
    time.sleep(0.5)
    
def get_cc_options():
    open_cc_options_list()
    time.sleep(1.25)
    cc_options = driver.find_elements_by_xpath(("//div[contains(@class, 'ytp-panel-menu')]/div[contains(@class, 'ytp-menuitem')]"))
    cc_options_labels = [option.find_element_by_xpath("div[contains(@class, 'ytp-menuitem-label')]").get_attribute("innerText") 
                         for option in cc_options]
    toggle_settings_menu()
    return cc_options_labels

def pick_cc_option(lang):
    open_cc_options_list()
    time.sleep(1.5)
    cc_options = driver.find_elements_by_xpath(("//div[contains(@class, 'ytp-panel-menu')]/div[contains(@class, 'ytp-menuitem')]"))
    cc_options_labels = [option.find_element_by_xpath("div[contains(@class, 'ytp-menuitem-label')]").get_attribute("innerText") 
                         for option in cc_options]
    cc_options[cc_options_labels.index(lang)].click()
    time.sleep(0.5)
    toggle_settings_menu()

def get_cc_text():
    try:
        cc_lines = driver.find_elements_by_xpath("//span[contains(@class, 'ytp-caption-segment')]")
        return " ".join([line.get_attribute("innerText") for line in cc_lines])
    except:
        return "~~~ !!! ERROR IN PARSING !!! ~~~"

def get_current_timecode():
    curr_time = driver.find_element_by_xpath("//div[contains(@class, 'ytp-time-display')]").get_attribute("innerText")
    timecode_re = re.compile("(([0-9]{1,2}:)?[0-9]{1,2}:[0-9]{2})")
    matches = timecode_re.findall(curr_time)
    return {"full": curr_time, "current": matches[0][0], "duration": matches[1][0]}

def parse_timecode(timecode):
    segments = [int(seg) for seg in re.compile("([0-9]{1,2})").findall(timecode)]
    if len(segments) == 3:
        return {"hours": segments[0],
                "minutes": segments[1],
                "seconds": segments[2],
                "total_seconds": segments[0] * 60 * 60 + segments[1] * 60 + segments[2]}
    elif len(segments) == 2:
        return {"hours": 0,
                "minutes": segments[0],
                "seconds": segments[1],
                "total_seconds": segments[0] * 60 + segments[1]}
    
def playing_status():
    return driver.find_element_by_xpath("//button[contains(@class, 'ytp-play-button')]").get_attribute("title")

def pause_video():
    if "Pause" in playing_status():
        driver.find_element_by_id('movie_player').send_keys("k")
        
def play_video():
    if "Play" in playing_status():
        driver.find_element_by_id('movie_player').send_keys("k")

def replay_video():
    if "Replay" in playing_status():
        driver.find_element_by_id('movie_player').send_keys("k")
        
def handle_ad(loud):
    skip_ad_text = driver.find_elements_by_xpath("//span[contains(@class, 'ytp-ad-preview-container')]")
    skip_ad_btn = driver.find_elements_by_xpath("//button[contains(@class, 'ytp-ad-skip-button')]")

    if loud:
        print(skip_ad_text)
        print(skip_ad_btn)
    
    if len(skip_ad_text) == 0 and len(skip_ad_btn) == 0:
        if loud:
            print("seems like no ad")
    elif len(skip_ad_btn) > 0:
        if len(skip_ad_text) > 0:
            while len(skip_ad_text[0].get_attribute("style")) == 0:
                print("waiting on skip ad button")
                time.sleep(2)  
        try:
            print("attempting to press skip ad")
            skip_ad_btn[0].click()
        except:
            print("can't press skip button for some reason")
    else:
        print("no luck on ads... waiting it out")
        time.sleep(30)

def scrape_video_caption_text(video_id):
    # navigate to video
    print("navigating to video")
    driver.get("https://www.youtube.com/watch?v=%s" % video_id)
    time.sleep(3)

    # init elements
    video = driver.find_element_by_id('movie_player')
    left_ctrls = driver.find_element_by_xpath("//div[contains(@class, 'ytp-left-controls')]")
    right_ctrls = driver.find_element_by_xpath("//div[contains(@class, 'ytp-right-controls')]")
    play_btn = left_ctrls.find_element_by_xpath("//button[contains(@class, 'ytp-play-button')]")

    # attempt to click large play button
    lg_play_btn = driver.find_elements_by_xpath("//button[contains(@class, 'ytp-large-play-button')]")
    if len(lg_play_btn) > 0:
        try:
            print("clicking large play button")
            lg_play_btn[0].click()
        except:
            print("tried clicking the big play button but no luck")

    # attempt to handle any ads
    handle_ad(True)
    time.sleep(2)

    # clear YT's popups
    try:
        left_ctrls.find_element_by_xpath("span[contains(@class, 'ytp-volume-area')]/button[contains(@class, 'ytp-mute-button')]").click()
    except:
        print("trying to clear popup in the way")
        promo = driver.find_element_by_xpath("//div[contains(@class, 'ytd-mealbar-promo-renderer')]")
        promo.find_element_by_xpath("div[contains(@class, 'button-container')]/*[1]").click()

    # go to beginning of video
    pause_video()
    video.send_keys("0")

    # mute video
    print("muting video")
    video.send_keys("m")

    # turn off autoplay
    print("turning off autoplay")
    right_ctrls.find_elements_by_xpath("button")[0].click()

    # get caption languages
    try:
        print("getting cc language options")
        cc_options = get_cc_options()
        cc_options_trim = [option for option in cc_options if "English" in option]
        print("Caption languages: %s" % cc_options_trim)
    except:
        print("No captions available... exiting...")
        return

    # quit out of function here if only looking for caption languages
    if 'capcheck' in parsed_args:
        print("Only checking for caption languages so stopping here...")
        print("Video has length of: %s" % get_current_timecode()["duration"])
        return()

    # scrape captions from video into cc_data array
    cc_data = [ ]
    for lang in cc_options_trim:
        print("Scraping captions for %s" % lang)
        pause_video()
        video.send_keys("0")
        time.sleep(1)
        pick_cc_option(lang)
        time.sleep(3)
        while "Replay" not in playing_status():
            time.sleep(0.25)
            play_video()
            time.sleep(0.5)
            handle_ad(False)
            pause_video()
            time.sleep(0.25)
            cc_obj = {"video_id": video_id,
                    "lang": lang, 
                    "text": get_cc_text(), 
                    "timecode": get_current_timecode()["full"]}
            print(cc_obj)
            cc_data.append(cc_obj)
            if (datetime.now() - start_time).seconds > (60 * 60 * 5.5):
                print("Video caption scraping taking longer than 5.5 hours... quitting...")
                return
        print("replaying video")
        replay_video()

    # save results to data folder
    df = pd.DataFrame(cc_data).drop_duplicates()
    print("saved %d queries as %d unique rows of cc data" % (len(cc_data), df.shape[0]))
    df.to_csv("data/caption_text/caption_text_%s.csv" % video_id, index = False)

#================#
# SET UP BROWSER #
#================#

# move to folder
if os.getcwd()[-11:] != "yt-captions":
    os.chdir("/Users/ben-tanen/Desktop/Projects/yt-captions")

# parse args (determine if file or single id)
parsed_args = parse_argv()

if 'file' in parsed_args:
    print('using file %s for ids' % parsed_args['file'])
    try:
        with open(parsed_args["file"], "r") as fp:
            lines_orig = fp.readlines()
            if 'capcheck' not in parsed_args:
                video_ids = [{"video_id": l.replace("\n", "").split("\t")[0],
                            "length": l.replace("\n", "").split("\t")[1]} for l in lines_orig]
                video_ids = [el["video_id"] for el in sorted(video_ids, key = lambda i: i["length"])]
            else:
                video_ids = [l.replace("\n", "").split("\t")[0] for l in lines_orig]
    except:
        print("failed to parse input file")
        sys.exit(1)
elif 'id' in parsed_args:
    print('using id %s' % parsed_args['id'])
    if len(parsed_args["id"]) != 11:
        print("provided video ID not proper format... exiting...")
        sys.exit(1)
    video_ids = [parsed_args['id']]
else:
    print("improper input provide (either need file or id)")
    sys.exit(1)

# check that video ids are of proper format
for video_id in video_ids:
    if len(video_id) != 11:
        print("provided video ID (%s) not proper format... exiting..." % video_id)
        sys.exit(1)

# only scrape caption_text from videos we don't already have
video_ids = [video_id for video_id in video_ids if "caption_text_%s.csv" % video_id not in os.listdir("data/caption_text/")]
if len(video_ids) == 0:
    print("no video ids left to scrape (none given or all already scraped)")
    sys.exit()

# limit to first 4 unscraped videos (so not to run over time on gh-actions)
if 'capcheck' not in parsed_args:
    video_ids = video_ids[:5]
print("video id(s): %s" % video_ids)

# start headless browser
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)

# start timer (only run for 5.5 hours max)
start_time = datetime.now()

# scrape caption text for each video id
for video_id in video_ids:
    try:
        print("==========================")
        print("scraping caption text from %s" % video_id)
        scrape_video_caption_text(video_id)
    except:
        print("failed to scrape caption text from %s" % video_id)
        traceback.print_exc()

# close driver
driver.quit()
