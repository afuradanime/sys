SELECT a.title, a_season.season, a_season.year
FROM anime a
INNER JOIN anime_season a_season ON a.id = a_season.anime_id
WHERE a_season.year = 2026 AND a_season.season = "WINTER";