CREATE TABLE anime_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO anime_type (name) VALUES 
    ('TV'),
    ('OVA'),
    ('Movie'),
    ('Special'),
    ('ONA'),
    ('Music');

CREATE TABLE anime_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO anime_status (name) VALUES 
    ('Finished Airing'),
    ('Currently Airing'),
    ('Not yet aired');

CREATE TABLE language (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO language (name) VALUES 
    ('Portuguese'),
    ('English');

CREATE TABLE anime (
    id INTEGER PRIMARY KEY,  -- MAL ID
    url TEXT,
    title TEXT NOT NULL,
    type_id INTEGER NOT NULL,
    source TEXT,
    episodes INTEGER,
    status_id INTEGER NOT NULL,
    airing BOOLEAN DEFAULT 0,
    duration TEXT,
    quality_score BOOLEAN DEFAULT 0,
    start_date DATETIME,
    end_date DATETIME,
    season TEXT,
    year INTEGER,
    broadcast_day TEXT,
    broadcast_time TEXT,
    broadcast_timezone TEXT,
    image_url TEXT,
    small_image_url TEXT,
    large_image_url TEXT,
    trailer_embed_url TEXT,
    
    FOREIGN KEY (type_id) REFERENCES anime_type(id),
    FOREIGN KEY (status_id) REFERENCES anime_status(id)
);

CREATE TABLE synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anime_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- 'Default', 'Japanese', 'English', 'Synonym'
    title TEXT NOT NULL,
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
);

CREATE TABLE anime_descriptions (
    anime_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (anime_id, language_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES language(id) ON DELETE CASCADE
);

CREATE TABLE producers (
    id INTEGER PRIMARY KEY,  -- MAL ID
    name TEXT UNIQUE NOT NULL,
    type TEXT,
    url TEXT
);

CREATE TABLE anime_producers (
    anime_id INTEGER NOT NULL,
    producer_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, producer_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
    FOREIGN KEY (producer_id) REFERENCES producers(id) ON DELETE CASCADE
);

CREATE TABLE licensors (
    id INTEGER PRIMARY KEY,  -- MAL ID
    name TEXT UNIQUE NOT NULL,
    type TEXT,
    url TEXT
);

CREATE TABLE anime_licensors (
    anime_id INTEGER NOT NULL,
    licensor_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, licensor_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
    FOREIGN KEY (licensor_id) REFERENCES licensors(id) ON DELETE CASCADE
);

CREATE TABLE studios (
    id INTEGER PRIMARY KEY,  -- MAL ID
    name TEXT UNIQUE NOT NULL,
    url TEXT
);

CREATE TABLE anime_studios (
    anime_id INTEGER NOT NULL,
    studio_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, studio_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
    FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY,  -- MAL ID
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- 'genre', 'theme', 'demographic', 'explicit_genre'
    url TEXT
);

CREATE TABLE anime_tags (
    anime_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, tag_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Index for filtering by anime season
CREATE INDEX idx_anime_year_season ON anime(year, season);
-- Index for filtering currently airing anime
CREATE INDEX idx_anime_airing ON anime(airing) WHERE airing = 1;
-- Index for title searching
CREATE INDEX idx_anime_title ON anime(title COLLATE NOCASE);
-- Index for looking up anime by any title variant
CREATE INDEX idx_synonyms_title ON synonyms(title COLLATE NOCASE);
CREATE INDEX idx_synonyms_anime_id ON synonyms(anime_id);
-- Index for finding anime by genre
CREATE INDEX idx_anime_tags_tag_id ON anime_tags(tag_id);
-- Index for getting all tags of an anime
CREATE INDEX idx_anime_tags_anime_id ON anime_tags(anime_id);
CREATE INDEX idx_tags_type_name ON tags(type, name);
-- Index for finding all anime by a studio
CREATE INDEX idx_anime_studios_studio_id ON anime_studios(studio_id);
CREATE INDEX idx_anime_studios_anime_id ON anime_studios(anime_id);
-- Index for getting descriptions by anime_id
CREATE INDEX idx_anime_descriptions_anime_id ON anime_descriptions(anime_id);
CREATE INDEX idx_anime_descriptions_language_id ON anime_descriptions(language_id);

-- Views
CREATE VIEW IF NOT EXISTS random_anime
AS
	SELECT a.id, a.url, a.title, a.type_id, a.source, a.episodes, a.status_id, a.airing, a.duration, a.start_date, a.end_date, a.season, a.year, a.broadcast_day, a.broadcast_time, a.broadcast_timezone, a.image_url, a.small_image_url, a.large_image_url, a.trailer_embed_url
    FROM anime a
    ORDER BY RANDOM() 
    LIMIT 1;