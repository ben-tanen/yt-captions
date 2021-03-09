#-----------------------------------------#
# PROJ: Calculate caption text similarity #
#-----------------------------------------#

### init environment
rm(list = ls())

library(tidyverse)
library(stringdist)

print(getwd())

if (!grepl("yt-captions(/)?$", getwd())) setwd("~/Desktop/Projects/yt-captions/")

path <- getwd()

# load in clean data file
for (file in list.files(paste0(path, "/data/caption_text/"), pattern = "_clean.csv")) {
  id <- gsub("_clean.csv", "", gsub("caption_text_", "", file))
  print(id)
  dt.raw <- read.csv(paste0(path, "/data/caption_text/", file)) %>%
    filter(text.user != "" | text.auto != "")
  print(paste0("overall similarity: ", 
               stringsim(tolower(paste0(dt.raw$text.user, collapse = " ")), 
                         tolower(paste0(dt.raw$text.auto, collapse = " ")))))
  
  print(paste0("similarity minus puncuation: ",
               stringsim(gsub("[[:punct:]]", "", tolower(paste0(dt.raw$text.user, collapse = " "))), 
                         gsub("[[:punct:]]", "", tolower(paste0(dt.raw$text.auto, collapse = " "))))))
  
  dt.w_matches <- dt.raw %>%
    mutate(exact_match = tolower(text.user) == tolower(text.auto),
           punctuation_less_match = gsub("[[:punct:]]", "", tolower(text.user)) == gsub("[[:punct:]]", "", tolower(text.auto)))
}


