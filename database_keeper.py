"""
The database keeper tool is a cmd line tool to maintain the anime database. 
It can sync with new releases, backup the database, and restore from a backup.
"""
import os
import configparser
import argparse
from pathlib import Path

# Config file for database keeper
CONFIG_FILE = "database_keeper.ini"
DEFAULT_DB_PATH = "../anime.db"

MENU = {
    "1": { "label": "Sync with new releases", "fn": lambda: exit(0)},
    "2": { "label": "Backup database", "fn": lambda: exit(0)},
    "3": { "label": "Restore from backup", "fn": lambda: exit(0)},
    "4": { "label": "Exit", "fn": lambda: exit(0)} 
};

def get_db_path():
    parser = argparse.ArgumentParser();
    parser.add_argument("--db-path", help="Path to the anime database");
    args, _ = parser.parse_known_args();

    if args.db_path:
        return args.db_path;

    cfg = configparser.ConfigParser();
    if Path(CONFIG_FILE).exists():
        cfg.read(CONFIG_FILE);
        return cfg.get("database", "path", fallback=DEFAULT_DB_PATH);

    return DEFAULT_DB_PATH;

def get_purpose():
    parser = argparse.ArgumentParser();
    parser.add_argument("--purpose", help="Purpose of running the database keeper", choices=["sync", "backup", "restore"]);
    args, _ = parser.parse_known_args();
    if args.purpose:
        return args.purpose;

    return None;

def __main__():
    print("Hello database keeper");

    # Load configurations
    db_path = get_db_path();
    print(f"Using database path: {db_path}");

    if not Path(db_path).exists():
        print(f"Database file not found at {db_path}. Please check the path and try again.");
        return;

    # What are we doin here
    # purpose = get_purpose();

    while True:

        for key, value in MENU.items():
            print(f"{key}: {value['label']}");

        choice = input("Select an option: ").strip();
        if choice in MENU:
            MENU[choice]["fn"]();
        else:
            print("Invalid choice. Please try again.");

if __name__ == "__main__":
    __main__();