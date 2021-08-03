library(tidyverse)

setwd("~/Desktop/Projects/yt-captions/")

to_consider <- read.table("data/setup/videos_to_consider_pull.txt", sep = "\t", quote = "") %>%
  as_tibble() %>%
  set_names(c("video_id", "length", "title"))

# after running python code to query to_consider videos:
# python code/scrape-captions-selenium.py --capcheck=t --file=data/setup/videos_to_consider_pull.txt > videos_to_consider_output.txt
lines.raw <- read.table("videos_to_consider_output.txt", sep = "\n")
lines <- tibble(line = lines.raw %>% slice(3:nrow(.)) %>% pull(V1)) %>%
  mutate(video_id = if_else(grepl("scraping caption text from", line),
                            str_extract(line, "([a-zA-Z0-9]|-|_){11}"),
                            ""),
         language = if_else(grepl("Caption languages: ", line),
                            str_extract(line, "\\[.*\\]"),
                            ""),
         length = if_else(grepl("Video has length of", line),
                          str_extract(line, "([0-9]+:)?[0-9]+:[0-9]{2}"),
                          ""),
         failed = if_else(grepl("failed to scrape caption text from", line), 1, 0),
         sep_line = if_else(grepl("^=+$", line), 1, 0),
         sep_line_gp = cumsum(sep_line))

lines.gp1 <- lines %>%
  group_by(sep_line_gp) %>%
  summarise(across(c(video_id, language, length, failed), c(n_distinct, max), .names = "{.col}_{.fn}")) %>%
  mutate(failed = failed_2 != 0 | video_id_1 != 2 | language_1 != 2 | length_1 != 2) %>%
  select(sep_line_gp, video_id = video_id_2, language = language_2, length = length_2, failed)

lines.gp2 <- lines.gp1 %>%
  tidylog::left_join(select(to_consider, video_id, title), by = "video_id") %>%
  mutate(language = gsub("\\[|\\]", "", language),
         language = gsub(", ", ",", language)) %>%
  separate(language, sep = ",", into = paste0("language", 1:5), remove = F, fill = "right") %>%
  mutate(too_few_langs = is.na(language2),
         too_many_langs = !is.na(language3),
         no_auto_gen = !grepl("auto-gen", language),
         .before = length) %>%
  separate(length, sep = ":", into = c("hours", "minutes", "seconds"), remove = F, fill = "left") %>%
  mutate(across(hours:seconds, as.numeric),
         across(hours:seconds, replace_na, replace = 0)) %>%
  mutate(too_long = hours > 0, .after = seconds) %>%
  mutate(failed = failed | too_few_langs | too_many_langs | no_auto_gen | too_long,
         length_str = glue::glue(paste0("{str_pad(hours, width = 2, side = 'left', pad = '0')}:",
                                        "{str_pad(minutes, width = 2, side = 'left', pad = '0')}:",
                                        "{str_pad(seconds, width = 2, side = 'left', pad = '0')}")),
         output_str = glue::glue(paste0("{video_id}  {length_str} {title}")))

lines.gp2 %>%
  tidylog::filter(!failed) %>%
  select(video_id, length_str, title) %>%
  write.table(file = "data/setup/videos_to_pull_caption_text.txt", sep = "\t", append = T, 
              row.names = F, col.names = F, quote = F)

lines.gp2 %>%
  tidylog::filter(failed) %>%
  select(video_id, length_str, title) %>%
  write.table(file = "data/setup/videos_not_to_pull_caption_text.txt", sep = "\t", append = T, 
              row.names = F, col.names = F, quote = F)
