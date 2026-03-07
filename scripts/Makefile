CC = python

TARGET_JSON = ../../data/anime_data_all.jsonl
RELATION_JSON = ../../data/anime_relations.jsonl
TARGET_DB = ../../anime.db

BACKUP_COUNT = 3

all: scrape build_database

backup:
	@echo "Creating backup of the database..."
	$(CC) backup_database.py --db-path $(TARGET_DB) --keep-count $(BACKUP_COUNT)

restore:
	@echo "Restoring the most recent backup of the database..."
	$(CC) backup_database.py --db-path $(TARGET_DB) --restore

scrape: scrape_anime scrape_relations

scrape_anime:
	@echo "Scraping anime data and saving to JSONL file..."

	# First pass scrape anime data
	$(CC) scraper.py --output $(TARGET_JSON) --scrape-target=anime

scrape_relations:
	@echo "Scraping relations data and saving to JSONL file..."

	# Second pass scrape relations data using the previously scraped anime data
	$(CC) scraper.py --output $(RELATION_JSON) --scrape-target=relations --anime-data=$(TARGET_JSON)

build_database: backup

	@echo "Building SQLite database from JSONL file..."
	$(CC) import_to_sqlite.py --input $(TARGET_JSON) --output $(TARGET_DB) --input-relations $(RELATION_JSON)

.PHONY: all scrape build_database backup scrape_anime scrape_relations