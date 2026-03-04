DELETE FROM anime
WHERE id NOT IN (
    SELECT MIN(id)
    FROM anime
    GROUP BY title
);
