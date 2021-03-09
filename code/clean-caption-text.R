#-----------------------------------------------------#
# PROJ: Clean YT caption text (for easier comparison) #
#-----------------------------------------------------#

### init environment
rm(list = ls())

library(dplyr)
library(data.table)
library(fuzzyjoin)

print(getwd())

if (!grepl("yt-captions(/)?$", getwd())) setwd("~/Desktop/Projects/yt-captions/")

path <- getwd()

### determine which caption_text files to clean
setwd(paste0(path, "/data/caption_text/"))
files.to_clean <- tibble(file = list.files(pattern = "caption_text_[A-z0-9]{11}.csv")) %>%
  mutate(id = gsub("caption_text_", "", gsub(".csv", "", file)),
         base = 1) %>%
  left_join(tibble(file = list.files(pattern = "caption_text_[A-z0-9]{11}_clean.csv")) %>%
              mutate(id = gsub("caption_text_", "", gsub("_clean.csv", "", file)),
                     clean = 1),
            by = "id", suffix = c(".base", ".clean")) %>%
  select(id, base, clean) %>%
  filter(is.na(clean))

print("file to clean:")
print(files.to_clean)

for (id in files.to_clean$id) {
  print(id)

  # import base file
  print("importing base file")
  dt.base.raw <- read.csv(paste0("caption_text_", id, ".csv")) %>%
    mutate(error_incident = grepl("ERROR IN PARSING", text),
           cont_error_incident = error_incident & shift(error_incident, n = 1, type = "lag"),
           current_timecode = gsub(" / ([0-9]|:)+$", "", timecode),
           current_timecode = format(as.POSIXct(current_timecode, format = "%M:%S"), "%H:%M:%S"),
           duration_timecode = gsub("([0-9]|:)+ / ", "", timecode),
           duration_timecode = format(as.POSIXct(duration_timecode, format = "%M:%S"), "%H:%M:%S"))
  print(paste0(nrow(dt.base.raw), " rows in dt.base.raw"))
  
  # report number of error incidents
  print(paste0(dt.base.raw %>% filter(error_incident) %>% nrow(), " error incidents... ",
               dt.base.raw %>% filter(cont_error_incident) %>% nrow(), " continued error incidents..."))
  stopifnot(dt.base.raw %>% filter(cont_error_incident) %>% nrow() < 1)
  print("removing errors, assuming gaps will be fine for coverage")
  
  # determine most common duration to remove weird ad queries
  durations <- dt.base.raw %>%
    count(duration_timecode, sort = T) %>%
    mutate(rank = row_number()) %>%
    filter(rank == 1)
  
  # remove error incidents as long as no continuious ones
  # and segments of ads
  dt.base <- dt.base.raw %>%
    filter(!error_incident) %>%
    inner_join(durations, by = "duration_timecode")
  
  # group captions together for user captions
  print("cleaning user captions")
  dt.user <- dt.base %>%
    filter(!grepl("auto-gen", lang)) %>%
    group_by(video_id, lang) %>%
    mutate(new_text = if_else(row_number() == 1, T, text != shift(text, n = 1, type = "lag")),
           text_gp = cumsum(new_text)) %>%
    ungroup() %>%
    group_by(video_id, lang, text, text_gp) %>%
    summarise(min_timecode = min(current_timecode),
              max_timecode = max(current_timecode),
              .groups = "drop") %>%
    arrange(video_id, lang, text_gp)
  print(paste0(nrow(dt.user), " rows in dt.user"))
  
  # function to determine what additional text was added for each query of
  # auto-gen captions
  addl_text <- function(t1, t2) {
    print(paste0(t1, " ~~~ ", t2))
    
    if (is.na(t1) & is.na(t2)) {
      return("")
    } else if (is.na(t1)) {
      return(t2)
    } else if (is.na(t2)) {
      return(t1)
    } else if (t1 == t2) {
      return("")
    }
    
    print("passed checks, attempting to calculate addl_text")
    
    print(t1)
    
    print(strsplit(t1, " "))
    
    t1_vec <- unlist(strsplit(t1, " "))
    
    print(t1_vec)
    
    for (i in 1:length(t1_vec)) {
      print(paste0("pattern ", i, ":"))
      pattern <- paste0("^\\Q", paste0(t1_vec[i:length(t1_vec)], collapse = " "), "\\E ")
      print(pattern)
      if (grepl(pattern, t2)) {
        print("successfuly found pattern")
        return(gsub(pattern, "", t2))
      }
    }
    return(t2)
  }
  addl_text_v <- Vectorize(addl_text)
  
  # determine unique new segments of text for each new auto-gen caption query
  print("cleaning auto captions")
  dt.auto <- dt.base %>%
    filter(grepl("auto-gen", lang)) %>%
    filter(row_number() < 5) %>%
    group_by(video_id) %>%
    mutate(prev_text = shift(text, n = 1, type = "lag"),
           new_text = if_else(!is.na(prev_text), 
                              addl_text_v(as.character(prev_text), as.character(text)), 
                              as.character(text))) %>%
    ungroup()
  print(paste0(nrow(dt.auto), " rows in dt.auto"))
  
  if (nrow(dt.auto) == 0) {
    print("no auto-generated captions, skipping...")
    next
  }
    
  # combine caption text together (auto + user)
  print("joining dt.user and dt.auto")
  dt.join <- dt.user %>%
    fuzzy_left_join(dt.auto %>%
                      select(video_id, text = new_text, timecode = current_timecode),
                    by = c("video_id", "min_timecode" = "timecode", "max_timecode" = "timecode"),
                    match_fun = c(`==`, `<=`, `>=`)) %>%
    select(video_id = video_id.x, min_timecode, max_timecode, text.user = text.x, text.auto = text.y, timecode) %>%
    filter((text.auto != "") | (text.auto == text.user)) %>%
    arrange(video_id, min_timecode, max_timecode, timecode) %>%
    group_by(video_id, text.auto, timecode) %>%
    mutate(text.auto.n = row_number()) %>%
    ungroup() %>%
    filter(text.auto.n == 1) %>%
    group_by(video_id, min_timecode, max_timecode, text.user) %>%
    summarise(text.auto = gsub("(^ +| +$)", "", gsub(" {2,}", " ", paste0(text.auto, collapse = " "))), .groups = "drop") %>%
    arrange(video_id, min_timecode, max_timecode)
  print(paste0(nrow(dt.join), " rows in dt.join"))
  
  # plot it (for visual check)
  # dt.join %>% 
  #   count(min = substr(min_timecode, 1, 5)) %>% 
  #   ggplot(aes(x = min, y = n)) + geom_col() + labs(title = id)
  
  # save the data
  write.csv(dt.join, paste0("caption_text_", id, "_clean.csv"), row.names = F)
}
