WITH src_corp_keyword AS (
    SELECT * FROM raw_data.corp_keyword
)
SELECT
    corpname,
    keyword
FROM
    src_corp_keyword