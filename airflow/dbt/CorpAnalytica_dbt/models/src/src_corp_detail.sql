WITH src_corp_detail AS (
    SELECT * FROM raw_data.corp_detail
)
SELECT
    crno,
    corpnm,
    enppbancmpynm,
    corpregmrktdcdnm,
    enpBsadr,
    enpDtadr,
    enpHmpgUrl,
    enpTlno
FROM
    src_corp_detail