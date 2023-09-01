WITH cd AS(
    SELECT * FROM {{ ref("src_corp_detail") }}
), cb AS (
    SELECT * FROM {{ ref("src_corp_basic") }}
), ck AS (
    SELECT * FROM {{ ref("src_corp_keyword") }}
)
SELECT DISTINCT ranked.temp_crno as crno, ranked.temp_entno as entno, ranked.temp_corpname as corpname,ranked.temp_public_corpname as public_corpname, ranked.temp_owner as owner, ranked.temp_address as address, ranked.temp_homepage_url as homepage_url, ranked.temp_phone_number as phone_number, ranked.temp_keyword as keyword
FROM(
    SELECT
        cd.crno as temp_crno,
        cb.entno as temp_entno,
        CASE WHEN cb.corpname IS NOT NULL THEN cb.corpname ELSE cd.corpnm END AS temp_corpname,
        cd.enpPbanCmpyNm as temp_public_corpname,
        cd.corpregmrktdcdnm as temp_owner,
        CONCAT(cd.enpBsadr, CONCAT(' ', cd.enpDtadr)) as temp_address,
        cd.enpHmpgUrl as temp_homepage_url,
        cd.enpTlno as temp_phone_number,
        ck.keyword as temp_keyword,
        rank() OVER (PARTITION BY temp_crno ORDER BY temp_entno, temp_corpname, temp_public_corpname, temp_owner,temp_address, temp_homepage_url, temp_phone_number, temp_keyword) as crno_ranked
    FROM cd
    LEFT OUTER JOIN cb
    ON cb.crno = cd.crno
    LEFT OUTER JOIN ck
    ON cb.corpname = ck.corpname
) as ranked
WHERE ranked.crno_ranked = 1
