SELECT a.title, d.description, a.episodes, a.type
FROM anime a
LEFT JOIN description d ON d.anime_id = a.id
WHERE d.ROWID IS NULL AND a.type = "TV"
ORDER BY a.episodes DESC;