#-----------------------------------------#
# PROJ: Calculate caption text similarity #
#-----------------------------------------#

### init environment
rm(list = ls())

library(tidyverse)
library(stringdist)
library(ggplot2)
library(ggbeeswarm)

print(getwd())

if (!grepl("yt-captions(/)?$", getwd())) setwd("~/Desktop/Projects/yt-captions/")

path <- getwd()

# get the clean files to use
dt <- tibble(file = list.files(paste0(path, "/data/caption_text/"), pattern = "_clean.csv")) %>%
  mutate(id = gsub("_clean.csv", "", gsub("caption_text_", "", file)))

# calculate overall similarity
dt$sim_overall <- NA
for (i in 301:nrow(dt)) {
  id <- dt$id[i]
  print(id)
  raw <- read.csv(paste0(path, "/data/caption_text/caption_text_", id, "_clean.csv")) %>%
    filter(text.user != "" | text.auto != "")
  score <- stringsim(tolower(paste0(raw$text.user, collapse = " ")), 
                     tolower(paste0(raw$text.auto, collapse = " ")))
  dt$sim_overall[i] <- score
}

# sim.overall <- lapply(dt$id, function(id) {
#   raw <- read.csv(paste0(path, "/data/caption_text/caption_text_", id, "_clean.csv")) %>%
#     filter(text.user != "" | text.auto != "")
#   score <- stringsim(tolower(paste0(raw$text.user, collapse = " ")), 
#                      tolower(paste0(raw$text.auto, collapse = " ")))
#   return(score)
# }) %>% set_names(dt$id)

# sim.wout_punct <- lapply(dt$id, function(id) {
#   raw <- read.csv(paste0(path, "/data/caption_text/caption_text_", id, "_clean.csv")) %>%
#     filter(text.user != "" | text.auto != "")
#   score <- stringsim(gsub("[[:punct:]]", "", tolower(paste0(raw$text.user, collapse = " "))), 
#                      gsub("[[:punct:]]", "", tolower(paste0(raw$text.auto, collapse = " "))))
#   return(score)
# }) %>% set_names(dt$id)

# add scores to dt
# dt$sim_overall <- unlist(sim.overall)
# dt$sim_wout_punct <- unlist(sim.wout_punct)

# look at quick summary stats
quantile(dt$sim_overall)
print(paste0("midpoint: ", (max(dt$sim_overall) + min(dt$sim_overall)) / 2))

quantile(dt$sim_wout_punct)
print(paste0("midpoint: ", (max(dt$sim_wout_punct) + min(dt$sim_wout_punct)) / 2))

# bucket scores
dt.w_bucket <- dt %>%
  mutate(bucket_overall = cut(sim_overall,
                              breaks = seq(0, 1, 0.1),
                              include.lowest = T),
         bucket_wout_punc = cut(sim_wout_punct,
                                breaks = seq(0, 1, 0.1),
                                include.lowest = T))

# plot it
ggplot(dt.w_bucket %>% 
         count(bucket = bucket_overall) %>%
         arrange(bucket)) +
  geom_col(aes(x = bucket, y = n))

ggplot(dt) +
  geom_beeswarm(aes(x = 0, y = sim_overall), cex = 2, size = 2) +
  scale_x_continuous(name = NULL, limits = c(-0.1, 0.1)) + 
  scale_y_continuous(name = "Overall caption similarity", limits = c(0, 1)) +
  coord_flip()

# dt.w_matches <- dt.raw %>%
#   mutate(exact_match = tolower(text.user) == tolower(text.auto),
#          punctuation_less_match = gsub("[[:punct:]]", "", tolower(text.user)) == gsub("[[:punct:]]", "", tolower(text.auto)))

