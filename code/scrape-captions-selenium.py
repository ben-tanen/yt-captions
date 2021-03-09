#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import pandas as pd

#=========================#
# DEFINE HELPER FUNCTIONS #
#=========================#

def exit_program(msg):
    print(msg)
    driver.quit()
    sys.exit(1)

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
    return play_btn.get_attribute("title")

def pause_video():
    if "Pause" in playing_status():
        # play_btn.click()
        video.send_keys("k")
        
def play_video():
    if "Play" in playing_status():
        video.send_keys("k")

def replay_video():
    if "Replay" in playing_status():
        video.send_keys("k")
        
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
    

#================#
# SET UP BROWSER #
#================#

# move to folder
if os.getcwd()[-11:] != "yt-captions":
    os.chdir("/Users/ben-tanen/Desktop/Projects/yt-captions")

# get video ID
if len(sys.argv) == 1:
    exit_program("No video IDs given... exiting...")
elif len(sys.argv) > 2:
    exit_program("More than one argument given... exiting...")
elif len(sys.argv[1]) != 11:
    exit_program("Provided video ID not proper format... exiting...")
    
video_id = sys.argv[1]

# start headless browser
driver = webdriver.Chrome(ChromeDriverManager().install())

#===================#
# NAVIGATE TO VIDEO #
#===================#

print("navigating to video")

driver.get("https://www.youtube.com/watch?v=%s" % video_id)

time.sleep(3)

video = driver.find_element_by_id('movie_player')
left_ctrls = driver.find_element_by_xpath("//div[contains(@class, 'ytp-left-controls')]")
right_ctrls = driver.find_element_by_xpath("//div[contains(@class, 'ytp-right-controls')]")
play_btn = left_ctrls.find_element_by_xpath("button[contains(@class, 'ytp-play-button')]")

#=======================#
# CHECK FOR PLAY BUTTON #
#=======================#

lg_play_btn = driver.find_elements_by_xpath("//button[contains(@class, 'ytp-large-play-button')]")
if len(lg_play_btn) > 0:
    try:
        print("clicking large play button")
        lg_play_btn[0].click()
    except:
        print("tried clicking the big play button but no luck")

#=====================================#
# CHECK FOR AD(s) AND ATTEMPT TO SKIP #
#=====================================#

handle_ad(True)
    
time.sleep(2)

#================#
# CLEAR YT POPUP #
#================#

try:
    left_ctrls.find_element_by_xpath("span[contains(@class, 'ytp-volume-area')]/button[contains(@class, 'ytp-mute-button')]").click()
except:
    print("trying to clear popup in the way")
    promo = driver.find_element_by_xpath("//div[contains(@class, 'ytd-mealbar-promo-renderer')]")
    promo.find_element_by_xpath("div[contains(@class, 'button-container')]/*[1]").click()

#================================#
# NAVIGATE TO BEGINNING OF VIDEO #
# AND SET UP LOOP                #
#================================#

# go to beginning of video
pause_video()
video.send_keys("0")

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
    exit_program("No captions available... exiting...")

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
    print("replaying video")
    replay_video()
  
df = pd.DataFrame(cc_data).drop_duplicates()

print("saved %d queries as %d unique rows of cc data" % (len(cc_data), df.shape[0]))

df.to_csv("data/caption_text/caption_text_%s.csv" % video_id, index = False)

driver.quit()
    




