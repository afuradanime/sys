CC = python

TARGET_JSON = ../../data/anime_data_all.jsonl
TARGET_DB = ../../anime.db

BACKUP_COUNT = 3

all: scrape build_database
scrape:
	@echo "Scraping anime data and saving to JSONL file..."
	$(CC) scraper.py --output $(TARGET_JSON)

build_database:
	@echo "Building SQLite database from JSONL file..."
	$(CC) import_to_sqlite.py --input $(TARGET_JSON) --output $(TARGET_DB)

backup:
	@echo "Creating backup of the database..."
	$(CC) backup_database.py --db-path $(TARGET_DB) --keep-count $(BACKUP_COUNT)

.PHONY: all scrape build_database backup