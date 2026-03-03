CC = python

TARGET_JSON = ../../data/anime_data_all.jsonl
TARGET_DB = ../../new_anime.db

all: scrape build_database

scrape:
	$(CC) scraper.py --output $(TARGET_JSON)

build_database:
	$(CC) import_to_sqlite.py --input $(TARGET_JSON) --output $(TARGET_DB)

.PHONY: all scrape build_database