WITH src_news_article AS (
    SELECT * FROM raw_data.news_article
)
SELECT
    id,
    corpname,
    link,
    article
FROM
    src_news_article