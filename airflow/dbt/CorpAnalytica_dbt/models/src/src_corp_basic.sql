WITH src_corp_basic AS (
    SELECT * FROM raw_data.corp_basic
)
SELECT
    entno,
    corpname,
    code,
    crno,
    stock_type
FROM
    src_corp_basic