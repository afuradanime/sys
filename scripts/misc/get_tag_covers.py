import csv
import time
import requests

CSV_FILE = "../_data/popular_tags.csv"
ANILIST_URL = "https://graphql.anilist.co"

ANILIST_GENRES = {
    "Action", "Adventure", "Comedy", "Drama", "Ecchi", "Fantasy",
    "Hentai", "Horror", "Mahou Shoujo", "Mecha", "Music", "Mystery",
    "Psychological", "Romance", "Sci-Fi", "Slice of Life", "Sports",
    "Supernatural", "Thriller"
}

GENRE_QUERY = """
query ($genre: String) {
  Page(page: 1, perPage: 1) {
    media(genre: $genre, sort: POPULARITY_DESC, type: ANIME) {
      title { romaji }
      coverImage { extraLarge }
    }
  }
}
"""

TAG_QUERY = """
query ($tag: String) {
  Page(page: 1, perPage: 1) {
    media(tag: $tag, sort: POPULARITY_DESC, type: ANIME) {
      title { romaji }
      coverImage { extraLarge }
    }
  }
}
"""

def query_anilist(query, variables, retries=5):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                ANILIST_URL,
                json={"query": query, "variables": variables},
                timeout=10
            )
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                print(f"  429 rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  Error: {e}, retry {attempt}/{retries}...")
            time.sleep(3 * attempt)
    return None

# Read genres from CSV
genres = []
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        genres.append({'id': int(row['id']), 'name': row['name']})

print(f"Loaded {len(genres)} genres\n")

results = []

for genre in genres:
    genre_id = genre['id']
    genre_name = genre['name']

    # Pick the right query
    if genre_name in ANILIST_GENRES:
        query = GENRE_QUERY
        variables = {"genre": genre_name}
    else:
        query = TAG_QUERY
        variables = {"tag": genre_name}

    image = ""
    try:
        data = query_anilist(query, variables)
        media = data["data"]["Page"]["media"]
        if media:
            title = media[0]["title"]["romaji"]
            image = media[0]["coverImage"]["extraLarge"]
            print(f"[{genre_id}] {genre_name} → {title}")
        else:
            print(f"[{genre_id}] {genre_name} → No results")
    except Exception as e:
        print(f"[{genre_id}] {genre_name} → FAILED: {e}")

    results.append((genre_id, genre_name, image))
    time.sleep(1.5)

# Output JS snippet
print("\n\n// JS Output:\n")
print("const mainGenres = [")
for genre_id, genre_name, image in results:
    print(f"    {{ id: {genre_id:<4}, /* {genre_name:<20} */ image: '{image}' }},")
print("]")