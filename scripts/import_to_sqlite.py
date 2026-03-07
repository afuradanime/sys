import os
import json
import sqlite3
from pathlib import Path
import configparser
from typing import Any, Dict, List, Optional
import sys
from datetime import datetime

CONFIG_FILE = "./import_config.ini";

DATABASE_MODEL: str = "./../sql/pm/physical_model_1.sql";
IMAGE_TYPE: str = "webp";
USE_QUALITY_FILTERING: bool = True;
QUALITY_TIERS: int = 3;
BLACKLISTED_TAGS: List[str] = [];
BLACKLISTED_TYPES: List[str] = [];

def create_tables(conn: sqlite3.Connection) -> None:
    """Create SQLite tables based on the new physical schema."""
    
    cursor = conn.cursor()
    
    # Drop existing tables (in correct order due to foreign keys)
    cursor.execute("DROP TABLE IF EXISTS anime_tags")
    cursor.execute("DROP TABLE IF EXISTS anime_studios")
    cursor.execute("DROP TABLE IF EXISTS anime_licensors")
    cursor.execute("DROP TABLE IF EXISTS anime_producers")
    cursor.execute("DROP TABLE IF EXISTS anime_descriptions")
    cursor.execute("DROP TABLE IF EXISTS synonyms")
    cursor.execute("DROP TABLE IF EXISTS tags")
    cursor.execute("DROP TABLE IF EXISTS studios")
    cursor.execute("DROP TABLE IF EXISTS licensors")
    cursor.execute("DROP TABLE IF EXISTS producers")
    cursor.execute("DROP TABLE IF EXISTS anime")
    cursor.execute("DROP TABLE IF EXISTS anime_status")
    cursor.execute("DROP TABLE IF EXISTS anime_type")
    
    model_text = Path(DATABASE_MODEL).read_text()
    cursor.executescript(model_text)
    
    conn.commit()
    print("Database schema created")

TIER_DIVISION = 10.0 / QUALITY_TIERS;
def calculate_quality_score(score: Optional[float]) -> int:
    if score is None or not USE_QUALITY_FILTERING:
        return -1;

    return int(score / TIER_DIVISION);

def blacklist_check(anime_data: Dict[str, Any]) -> bool:
    """Check if anime should be blacklisted based on tags and type."""

    if anime_data.get('type', '') == None:
        return False;

    anime_type = anime_data.get('type', '').lower()
    if anime_type in (t.lower() for t in BLACKLISTED_TYPES):
        return True

    all_tags = []
    for field in ['genres', 'themes', 'demographics', 'explicit_genres']:
        tags = anime_data.get(field, [])
        if isinstance(tags, list):
            all_tags.extend(tags)

    for tag in all_tags:

        if tag.get('name') == None:
            continue;

        tag_name = tag.get('name', '').lower()
        if tag_name in (t.lower() for t in BLACKLISTED_TAGS):
            return True

    return False

def get_or_create_type_id(cursor: sqlite3.Cursor, type_name: str) -> int:
    """Get type_id from anime_type table."""
    if not type_name:
        return 7  # Unknown
    cursor.execute("SELECT id FROM anime_type WHERE name = ?", (type_name,))
    result = cursor.fetchone()
    return result[0] if result else 7


def get_or_create_status_id(cursor: sqlite3.Cursor, status_name: str) -> int:
    """Get status_id from anime_status table."""
    if not status_name:
        return 4  # Unknown
    cursor.execute("SELECT id FROM anime_status WHERE name = ?", (status_name,))
    result = cursor.fetchone()
    return result[0] if result else 4


def insert_or_get_entity(cursor: sqlite3.Cursor, table: str, 
                         entity_data: Dict[str, Any]) -> Optional[int]:
    """Insert or get existing entity (producer, licensor, studio, tag)."""
    mal_id = entity_data.get('mal_id')
    name = entity_data.get('name')
    entity_type = entity_data.get('type')
    url = entity_data.get('url')
    
    if not mal_id or not name:
        return None
    
    # Try to get existing entity by MAL ID
    cursor.execute(f"SELECT id FROM {table} WHERE id = ?", (mal_id,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Insert new entity
    try:
        if table == 'tags':
            # For tags, we also need to store the type (genre, theme, demographic, explicit_genre)
            cursor.execute(f"""
                INSERT INTO {table} (id, name, type, url)
                VALUES (?, ?, ?, ?)
            """, (mal_id, name, entity_type, url))
        else:
            cursor.execute(f"""
                INSERT INTO {table} (id, name, url)
                VALUES (?, ?, ?)
            """, (mal_id, name, url))
        return mal_id
    except sqlite3.IntegrityError:
        cursor.execute(f"SELECT id FROM {table} WHERE id = ?", (mal_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def insert_anime(conn: sqlite3.Connection, anime_data: Dict[str, Any]) -> Optional[int]:
    """Insert anime record and all related data."""
    cursor = conn.cursor()
    
    try:
        # Extract basic info
        mal_id = anime_data.get('id')
        if not mal_id:
            print(f"Warning: Skipping anime without mal_id", file=sys.stderr)
            return None
        
        url = anime_data.get('url')
        title = anime_data.get('title')
        if not title:
            print(f"Warning: Skipping anime {mal_id} without title", file=sys.stderr)
            return None
            
        source = anime_data.get('source')
        
        # Type and status (convert to IDs)
        anime_type = anime_data.get('type')
        type_id = get_or_create_type_id(cursor, anime_type)
        
        status = anime_data.get('status')
        status_id = get_or_create_status_id(cursor, status)
        
        # Episodes and airing
        episodes = anime_data.get('episodes')
        airing = 1 if anime_data.get('airing', False) else 0
        duration = anime_data.get('duration')
        
        # Quality score flag
        score = anime_data.get('score')
        quality_score = calculate_quality_score(score);
        
        # Dates
        start_date = anime_data.get('start_date')
        end_date = anime_data.get('end_date')
        season = anime_data.get('season')
        year = anime_data.get('year')
        
        # Broadcast
        broadcast_day = anime_data.get('broadcast_day')
        broadcast_time = anime_data.get('broadcast_time')
        broadcast_timezone = anime_data.get('broadcast_timezone')
        
        # Images
        image_url = anime_data.get(f'{IMAGE_TYPE}_image_url') or anime_data.get('image_url')
        small_image_url = anime_data.get(f'{IMAGE_TYPE}_small_image_url') or anime_data.get('small_image_url')
        large_image_url = anime_data.get(f'{IMAGE_TYPE}_large_image_url') or anime_data.get('large_image_url')
        
        # Trailer
        trailer_embed_url = anime_data.get('trailer_embed_url')

        if blacklist_check(anime_data):
            # print(f"Skipping blacklisted anime: {title} (ID: {mal_id})", file=sys.stderr);
            return None;
        
        # Insert main anime record
        cursor.execute("""
            INSERT OR REPLACE INTO anime 
            (id, url, title, type_id, source, episodes, status_id, airing, 
             duration, quality_score, start_date, end_date, season, year,
             broadcast_day, broadcast_time, broadcast_timezone,
             image_url, small_image_url, large_image_url,
             trailer_embed_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (mal_id, url, title, type_id, source, episodes, status_id, airing,
              duration, quality_score, start_date, end_date, season, year,
              broadcast_day, broadcast_time, broadcast_timezone,
              image_url, small_image_url, large_image_url,
              trailer_embed_url))
        
        # Combine synopsis and background for description
        synopsis = anime_data.get('synopsis', '')
        background = anime_data.get('background', '')
        
        # Build combined description
        description_parts = []
        if synopsis:
            description_parts.append(synopsis)
        if background:
            description_parts.append(f"\n\n{background}")
        
        combined_description = ''.join(description_parts)
        
        # Insert description 
        if combined_description:
            cursor.execute("""
                INSERT OR REPLACE INTO anime_descriptions (anime_id, description)
                VALUES (?, ?)
            """, (mal_id, combined_description))
        
        # Insert title variants
        titles = anime_data.get('titles', [])
        for title_entry in titles:
            if not isinstance(title_entry, dict):
                continue
            title_type = title_entry.get('type')
            title_text = title_entry.get('title')
            if title_text and title_type != "Default":
                cursor.execute("""
                    INSERT INTO synonyms (anime_id, type, title)
                    VALUES (?, ?, ?)
                """, (mal_id, title_type, title_text))

        # Insert title synonyms separately
        title_synonyms = anime_data.get('title_synonyms', [])
        existing_titles = {t.get('title') for t in titles if t.get('title')}
        for synonym in title_synonyms:
            if synonym and isinstance(synonym, str) and synonym not in existing_titles:
                cursor.execute("""
                    INSERT INTO synonyms (anime_id, type, title)
                    VALUES (?, ?, ?)
                """, (mal_id, 'Synonym', synonym))
        
        # Insert producers
        producers = anime_data.get('producers', [])
        for producer in producers:
            if not isinstance(producer, dict):
                continue
            producer_id = insert_or_get_entity(cursor, 'producers', producer)
            if producer_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO anime_producers (anime_id, producer_id)
                    VALUES (?, ?)
                """, (mal_id, producer_id))
        
        # Insert licensors
        licensors = anime_data.get('licensors', [])
        for licensor in licensors:
            if not isinstance(licensor, dict):
                continue
            licensor_id = insert_or_get_entity(cursor, 'licensors', licensor)
            if licensor_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO anime_licensors (anime_id, licensor_id)
                    VALUES (?, ?)
                """, (mal_id, licensor_id))
        
        # Insert studios
        studios = anime_data.get('studios', [])
        for studio in studios:
            if not isinstance(studio, dict):
                continue
            studio_id = insert_or_get_entity(cursor, 'studios', studio)
            if studio_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO anime_studios (anime_id, studio_id)
                    VALUES (?, ?)
                """, (mal_id, studio_id))
        
        # Insert tags (genres, themes, demographics, explicit_genres)
        tag_types = [
            ('genres', 'genre'),
            ('themes', 'theme'),
            ('demographics', 'demographic'),
            ('explicit_genres', 'explicit_genre')
        ]
        
        for field_name, tag_type in tag_types:
            tags = anime_data.get(field_name, [])
            for tag in tags:
                if not isinstance(tag, dict):
                    continue
                tag_id = insert_or_get_entity(cursor, 'tags', {
                    'mal_id': tag.get('mal_id'),
                    'name': tag.get('name'),
                    'type': tag_type,
                    'url': tag.get('url')
                })
                if tag_id:
                    cursor.execute("""
                        INSERT OR IGNORE INTO anime_tags (anime_id, tag_id)
                        VALUES (?, ?)
                    """, (mal_id, tag_id))
        
        return mal_id
        
    except Exception as e:
        print(f"Error inserting anime {anime_data.get('id') or anime_data.get('mal_id')}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def import_json_to_sqlite(json_path: Path, db_path: Path) -> None:
    """Import JSON data into SQLite database."""
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    
    create_tables(conn)
    
    total_records = 0
    error_count = 0
    skip_count = 0;
    
    try:
        print(f"\nReading from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            # Handle both JSONL (line by line) and JSON array formats
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                # JSON array format
                data = json.load(f)
                anime_list = data if isinstance(data, list) else [data]
            else:
                # JSONL format
                anime_list = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            anime_list.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        
        print(f"Found {len(anime_list)} anime records to import\n")
        
        for anime_data in anime_list:
            try:
                anime_id = insert_anime(conn, anime_data)
                if anime_id:
                    total_records += 1
                    
                    if total_records % 1000 == 0:
                        print(f"Processed {total_records} records...")
                        conn.commit()
                else:
                    skip_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing anime: {e}", file=sys.stderr)
        
        conn.commit()
        
        # Print statistics
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM anime")
        anime_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM studios")
        studio_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        
        print(f"\n{'='*50}")
        print(f"Import complete!")
        print(f"{'='*50}")
        print(f"  Anime imported:          {total_records}")
        print(f"  Errors encountered:      {error_count}")
        print(f"  Records skipped:         {skip_count}")
        print(f"  Total anime in DB:       {anime_count}")
        print(f"  Unique studios:          {studio_count}")
        print(f"  Unique tags:             {tag_count}")
        print(f"{'='*50}\n")
        
    except FileNotFoundError:
        print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


def import_json_relations_to_sqlite(json_path: Path, db_path: Path) -> None:
    """Import anime relations from JSON into SQLite database."""
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    
    total_relations = 0
    error_count = 0
    
    try:
        print(f"\nReading relations from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                data = json.load(f)
                relations_list = data if isinstance(data, list) else [data]
            else:
                relations_list = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            relations_list.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        
        print(f"Found {len(relations_list)} anime relations to import\n")
        
        cursor = conn.cursor()
        
        for relation_data in relations_list:
            try:
                anime_id = relation_data.get('anime_id')
                related_anime_id_list = relation_data.get('related_anime', [])
                relation_type = relation_data.get('relation_type')
                
                if not anime_id or not related_anime_id_list or not relation_type:
                    continue

                # Check if anime ID exists in DB
                cursor.execute("SELECT 1 FROM anime WHERE id = ?", (anime_id,))
                if not cursor.fetchone():
                    continue;

                # Get relation_type_id from relation_types table
                cursor.execute("SELECT id FROM relation_types WHERE name = ?", (relation_type,))
                relation_type_id = cursor.fetchone()
                if not relation_type_id:
                    # If the relation type doesn't exist, skip it
                    print(f"Unknown relation type: {relation_type}, skipping.")
                    continue
                relation_type_id = relation_type_id[0]  # Extract ID

                # Insert relations into anime_relations table
                for related_anime in related_anime_id_list:
                    # Skip manga for now
                    if related_anime.get('type') != 'anime':
                        continue;

                    related_anime_id = related_anime.get('mal_id');

                    # check related anime exists
                    cursor.execute("SELECT 1 FROM anime WHERE id = ?", (related_anime_id,))
                    if not cursor.fetchone():
                        continue
                    
                    # Insert the relation into anime_relations
                    # It seems there are repeats?
                    cursor.execute("""
                        INSERT OR IGNORE INTO anime_relations (anime_id, relation_type_id, related_anime_id)
                        VALUES (?, ?, ?)
                    """, (anime_id, relation_type_id, related_anime_id))
                
                total_relations += 1
                
                if total_relations % 1000 == 0:
                    print(f"Processed {total_relations} relations...")
                    conn.commit()
            except Exception as e:
                error_count += 1
                print(f"Error processing relation: {e}", file=sys.stderr)
        
        conn.commit()
        
        print(f"\n{'='*50}")
        print(f"Relations import complete!")
        print(f"{'='*50}")
        print(f"  Relations imported:      {total_relations}")
        print(f"  Errors encountered:      {error_count}")
        print(f"{'='*50}\n")
    
    except Exception as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr);
        conn.rollback();
        sys.exit(1);
    finally:
        conn.close();

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import MyAnimeList API data into SQLite using new physical model"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSON/JSONL input file"
    )

    parser.add_argument(
        "--input-relations",
        type=Path,
        required=False,
        help="Path to JSON/JSONL input file for anime relations (optional)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("anime.db"),
        help="Path to SQLite database file (default: anime.db)"
    )
    
    args = parser.parse_args()

    if os.path.exists(args.output):
        print(f"Warning: Output database file already exists, renaming to {args.output}.old");
        try:
            if args.output.with_suffix('.db.old').exists():
                os.remove(args.output.with_suffix('.db.old'));

            os.rename(args.output, args.output.with_suffix('.db.old'));
            print(f"Renamed existing database to {args.output.with_suffix('.db.old')}");
        except Exception as e:
            print(f"Error renaming existing database: {e}", file=sys.stderr);
            sys.exit(1);
    
    cfg = configparser.ConfigParser()
    if Path(CONFIG_FILE).exists():
        cfg.read(CONFIG_FILE);
        
        global IMAGE_TYPE, USE_QUALITY_FILTERING, QUALITY_TIERS, BLACKLISTED_TAGS, BLACKLISTED_TYPES, DATABASE_MODEL;
        
        DATABASE_MODEL = cfg.get("Database", "import_script", fallback=DATABASE_MODEL);
        IMAGE_TYPE = cfg.get("Import", "image_type", fallback=IMAGE_TYPE);
        
        USE_QUALITY_FILTERING = cfg.getboolean("Import", "use_quality_filtering", fallback=USE_QUALITY_FILTERING);
        QUALITY_TIERS = cfg.getint("Import", "quality_tiers", fallback=QUALITY_TIERS);
        
        BLACKLISTED_TAGS = json.loads(cfg.get("Import", "blacklisted_tags", fallback="[]"));
        BLACKLISTED_TYPES = json.loads(cfg.get("Import", "blacklisted_types", fallback="[]"));
    else:
        print(f"Warning: Config file {CONFIG_FILE} not found, using default settings.", file=sys.stderr);

    print(f"\n{'='*50}")
    print(f"Anime Database Import Tool")
    print(f"{'='*50}")
    print(f"Input file:  {args.input}")
    print(f"Output DB:   {args.output}")

    print(f"\nConfiguration:")
    print(f"  Database model:          {DATABASE_MODEL}")
    print(f"  Image type:              {IMAGE_TYPE}")
    print(f"  Use quality filtering:   {USE_QUALITY_FILTERING}")
    print(f"  Quality tiers:           {QUALITY_TIERS}")
    print(f"  Blacklisted tags:        {BLACKLISTED_TAGS}")
    print(f"  Blacklisted types:       {BLACKLISTED_TYPES}")

    print(f"{'='*50}\n")
    
    import_json_to_sqlite(args.input, args.output)

    # Only import relations if the file is provided
    if args.input_relations and os.path.exists(args.input_relations):
        import_json_relations_to_sqlite(args.input_relations, args.output);
    else:
        print(f"No relations file provided or file does not exist, skipping relations import.");

if __name__ == "__main__":
    main()