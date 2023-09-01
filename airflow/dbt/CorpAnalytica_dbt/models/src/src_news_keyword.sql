WITH src_news_keyword AS (
    SELECT * FROM raw_data.news_keyword
)
SELECT
    id,
    corpname,
    link,
    keyword,
    summary_sentence1,
    summary_sentence2,
    summary_sentence3
FROM
    src_news_keyword