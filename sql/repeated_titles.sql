SELECT a.title, COUNT(*), a.id
FROM anime a
GROUP BY a.title
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC