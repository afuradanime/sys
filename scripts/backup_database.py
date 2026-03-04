import argparse;
from pathlib import Path;
import time;

def backup_cloud(db_path: Path):
    pass;

def delete_old_backups(keep_count: int = 1):

    backup_folder = Path("./backups");
    if not backup_folder.exists():
        print("No backup folder found. Skipping old backup deletion.");
        return;

    backup_files = sorted(backup_folder.glob("*.backup"), key=lambda f: f.stat().st_mtime, reverse=True);
    if len(backup_files) <= keep_count:
        print("No old backups to delete.");
        return;

    for old_backup in backup_files[keep_count:]:
        try:
            old_backup.unlink();
            print(f"Deleted old backup: {old_backup}");
        except Exception as e:
            print(f"Error deleting old backup {old_backup}: {e}");

def backup_local(db_path: Path):

    date_string = time.strftime("%Y%m%d-%H%M%S");
    backup_path = Path("./backups/" + db_path.name + "-" + date_string + ".backup");
    try:
        with db_path.open("rb") as src, backup_path.open("wb") as dst:
            dst.write(src.read());
        print(f"Database backed up successfully to {backup_path}");
    except Exception as e:
        print(f"Error backing up database: {e}");

def main():
    
    parser = argparse.ArgumentParser(
        description="Backup database"
    );

    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="Path to database file"
    );

    # parser.add_argument(
    #     "--local",
    #     action="store_true",
    #     help="Backup locally instead of cloud"
    # );

    parser.add_argument(
        "--keep-count",
        type=int,
        default=0,
        help="Number of old backups to keep (local backup only)"
    )

    args = parser.parse_args();
    
    if not args.db_path.exists():
        print(f"Database file not found at {args.db_path}. Please check the path and try again.");
        return;

    backup_local(args.db_path);

    if args.keep_count > 0:
        delete_old_backups(args.keep_count);

if __name__ == "__main__":
    main()