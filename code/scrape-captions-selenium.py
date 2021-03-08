#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, time, re
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
    time.sleep(0.5)
    cc_options = driver.find_elements_by_xpath(("//div[contains(@class, 'ytp-panel-menu')]/div[contains(@class, 'ytp-menuitem')]"))
    cc_options_labels = [option.find_element_by_xpath("div[contains(@class, 'ytp-menuitem-label')]").get_attribute("innerText") 
                         for option in cc_options]
    toggle_settings_menu()
    return cc_options_labels

def pick_cc_option(lang):
    open_cc_options_list()
    cc_options = driver.find_elements_by_xpath(("//div[contains(@class, 'ytp-panel-menu')]/div[contains(@class, 'ytp-menuitem')]"))
    cc_options_labels = [option.find_element_by_xpath("div[contains(@class, 'ytp-menuitem-label')]").get_attribute("innerText") 
                         for option in cc_options]
    cc_options[cc_options_labels.index(lang)].click()
    time.sleep(0.5)
    toggle_settings_menu()

def get_cc_text():
    cc_lines = driver.find_elements_by_xpath("//span[contains(@class, 'ytp-caption-segment')]")
    return " ".join([line.get_attribute("innerText") for line in cc_lines])

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
    
def is_playing():
    t0 = get_current_timecode()
    time.sleep(1)
    t1 = get_current_timecode()
    return t0['full'] != t1['full']

def pause_video():
    if is_playing():
        video.send_keys(Keys.SPACE)
        
def play_video():
    if not is_playing():
        video.send_keys(Keys.SPACE)

#================#
# SET UP BROWSER #
#================#

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

#=======================#
# CHECK FOR PLAY BUTTON #
#=======================#

lg_play_btn = driver.find_elements_by_xpath("//button[contains(@class, 'ytp-large-play-button')]")
if len(lg_play_btn) > 0:
    try:
        lg_play_btn[0].click()
    except:
        print("tried clicking the big play button but no luck")

#=====================================#
# CHECK FOR AD(s) AND ATTEMPT TO SKIP #
#=====================================#

# ytp-ad-preview-container
# ytp-ad-preview-container countdown-next-to-thumbnail

skip_ad_text = driver.find_elements_by_xpath("//span[contains(@class, 'ytp-ad-preview-container')]")
skip_ad_btn = driver.find_elements_by_xpath("//button[contains(@class, 'ytp-ad-skip-button')]")

print(skip_ad_text)
print(skip_ad_btn)

if len(skip_ad_text) == 0 and len(skip_ad_btn) == 0:
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
    time.sleep(30)
    
time.sleep(2)

#================================#
# NAVIGATE TO BEGINNING OF VIDEO #
# AND SET UP LOOP                #
#================================#

# go to beginning of video
pause_video()
video.send_keys("0")

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
    while get_current_timecode()["current"] != get_current_timecode()["duration"]:
        video.send_keys(Keys.SPACE)
        time.sleep(0.5)
        video.send_keys(Keys.SPACE)
        time.sleep(0.25)
        cc_obj = {"videoURL": driver.current_url,
                  "lang": lang, 
                  "text": get_cc_text(), 
                  "timecode": get_current_timecode()["full"]}
        print(cc_obj)
        cc_data.append(cc_obj)
        time.sleep(0.25)
  
df = pd.DataFrame(cc_data).drop_duplicates()

print("saved %d queries as %d unique rows of cc data" % (len(cc_data), df.shape[0]))

df.to_csv("data/captions/captions_%s.csv" % video_id, index = False)

driver.quit()
    




