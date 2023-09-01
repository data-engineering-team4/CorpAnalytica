WITH src_naver_news AS (
    SELECT * FROM raw_data.naver_news
)
SELECT
    id,
    code,
    corpname,
    title,
    link,
    description,
    pubdate
FROM
    src_naver_news