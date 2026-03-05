SELECT t.name, COUNT(at.anime_id)
FROM tags t
INNER JOIN anime_tags at ON at.tag_id = t.id
GROUP BY t.name
ORDER BY COUNT(at.anime_id) DESC