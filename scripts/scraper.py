import requests
import json
import time
from typing import Dict, Any, List

BASE_URL = "https://api.jikan.moe/v4/anime"

def extract_anime_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms raw API data into the Clean Domain Model.
    """
    # Basic info
    mal_id = raw_data.get('mal_id')
    url = raw_data.get('url')
    approved = raw_data.get('approved', False)
    
    # Titles
    title = raw_data.get('title')
    title_english = raw_data.get('title_english')
    title_japanese = raw_data.get('title_japanese')
    title_synonyms = raw_data.get('title_synonyms', [])
    titles = raw_data.get('titles', [])
    
    # Type and source
    anime_type = raw_data.get('type')
    source = raw_data.get('source')
    
    # Episodes and status
    episodes = raw_data.get('episodes')
    status = raw_data.get('status')
    airing = raw_data.get('airing', False)
    
    # Dates
    aired = raw_data.get('aired', {})
    start_date = aired.get('from')
    end_date = aired.get('to')
    aired_string = aired.get('string')
    season = raw_data.get('season')
    year = raw_data.get('year')
    
    # Broadcast
    broadcast = raw_data.get('broadcast', {})
    broadcast_day = broadcast.get('day')
    broadcast_time = broadcast.get('time')
    broadcast_timezone = broadcast.get('timezone')
    broadcast_string = broadcast.get('string')
    
    # Duration and rating
    duration = raw_data.get('duration')
    rating = raw_data.get('rating')
    
    # Images
    images = raw_data.get('images', {})
    jpg_images = images.get('jpg', {})
    webp_images = images.get('webp', {})
    
    # Trailer
    trailer = raw_data.get('trailer', {})
    trailer_youtube_id = trailer.get('youtube_id')
    trailer_url = trailer.get('url')
    trailer_embed_url = trailer.get('embed_url')
    
    # Scores and statistics
    score = raw_data.get('score')
    scored_by = raw_data.get('scored_by')
    rank = raw_data.get('rank')
    popularity = raw_data.get('popularity')
    members = raw_data.get('members')
    favorites = raw_data.get('favorites')
    
    # Text content
    synopsis = raw_data.get('synopsis')
    background = raw_data.get('background')
    
    # Related entities
    producers = raw_data.get('producers', [])
    licensors = raw_data.get('licensors', [])
    studios = raw_data.get('studios', [])
    genres = raw_data.get('genres', [])
    explicit_genres = raw_data.get('explicit_genres', [])
    themes = raw_data.get('themes', [])
    demographics = raw_data.get('demographics', [])
    
    return {
        # Basic identification
        "id": mal_id,
        "url": url,
        "approved": approved,
        
        # Titles
        "title": title,
        "title_english": title_english,
        "title_japanese": title_japanese,
        "title_synonyms": title_synonyms,
        "titles": titles,
        
        # Type and source
        "type": anime_type,
        "source": source,
        
        # Episodes and status
        "episodes": episodes,
        "status": status,
        "airing": airing,
        
        # Dates
        "start_date": start_date,
        "end_date": end_date,
        "aired_string": aired_string,
        "season": season,
        "year": year,
        
        # Broadcast
        "broadcast_day": broadcast_day,
        "broadcast_time": broadcast_time,
        "broadcast_timezone": broadcast_timezone,
        "broadcast_string": broadcast_string,
        
        # Duration and rating
        "duration": duration,
        "rating": rating,
        
        # Images (JPG)
        "image_url": jpg_images.get('image_url'),
        "small_image_url": jpg_images.get('small_image_url'),
        "large_image_url": jpg_images.get('large_image_url'),
        
        # Images (WebP)
        "webp_image_url": webp_images.get('image_url'),
        "webp_small_image_url": webp_images.get('small_image_url'),
        "webp_large_image_url": webp_images.get('large_image_url'),
        
        # Trailer
        "trailer_youtube_id": trailer_youtube_id,
        "trailer_url": trailer_url,
        "trailer_embed_url": trailer_embed_url,
        
        # Scores and statistics
        "score": score,
        "scored_by": scored_by,
        "rank": rank,
        "popularity": popularity,
        "members": members,
        "favorites": favorites,
        
        # Text content
        "synopsis": synopsis,
        "background": background,
        
        # Related entities (full objects with mal_id, name, type, url)
        "producers": producers,
        "licensors": licensors,
        "studios": studios,
        "genres": genres,
        "explicit_genres": explicit_genres,
        "themes": themes,
        "demographics": demographics
    }

def run_scraper(output_file: str):
    page = 1
    total_saved = 0
    consecutive_errors = 0
    
    print("Starting scraper. Press Ctrl+C to stop manually.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        while True:
            try:
                # print(f"Fetching page {page}...", end='\r') # Optional: Keep console clean
                
                response = requests.get(f"{BASE_URL}?page={page}")
                
                # Handling Rate Limits (429)
                if response.status_code == 429:
                    print(f"\nRate limit hit on page {page}. Sleeping for 10 seconds...")
                    time.sleep(10)
                    continue
                
                # Handling Server Errors (500s)
                if response.status_code >= 500:
                    print(f"\nServer error {response.status_code} on page {page}. Retrying...")
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        print("Too many errors. Aborting.")
                        break
                    time.sleep(10)
                    continue

                response.raise_for_status()
                consecutive_errors = 0 # Reset error count on success
                
                payload = response.json()
                anime_list = payload.get('data', [])
                pagination = payload.get('pagination', {})
                
                if not anime_list:
                    print(f"\nNo data found on page {page}. Stopping.")
                    break
                
                # Process the page
                for raw_anime in anime_list:
                    processed_anime = extract_anime_data(raw_anime)
                    json_line = json.dumps(processed_anime, ensure_ascii=False)
                    f.write(json_line + "\n")
                    total_saved += 1
                    
                    # THE MILESTONE PRINT
                    if total_saved % 1000 == 0:
                        print(f"\n--- {total_saved} entries saved! ---")

                # Check if there is a next page
                if not pagination.get('has_next_page'):
                    print("\nReached the last page.")
                    break
                
                page += 1
                
                time.sleep(1) 
                
            except KeyboardInterrupt:
                print("\nScraper stopped by user.")
                break
            except Exception as e:
                print(f"\nUnexpected error on page {page}: {e}")
                time.sleep(5)

    print(f"\nDone! Total anime saved: {total_saved}")
    print(f"Data stored in {output_file}")

if __name__ == "__main__":

    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="Scrape MAL data from jikan"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("anime_data_all.jsonl"),
        help="Path to output json file (default: anime_data_all.jsonl)"
    )
    
    args = parser.parse_args()

    run_scraper(args.output)