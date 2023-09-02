with co_ke1 AS (SELECT 
    corpname,
    REPLACE(REPLACE(REPLACE(keyword, '[', ''), ']', ''), '''', '') AS cleaned_string,
    SPLIT_PART(cleaned_string, ',', 1) AS corp_word1,
    SPLIT_PART(cleaned_string, ',', 2) AS corp_word2,
    SPLIT_PART(cleaned_string, ',', 3) AS corp_word3,
    SPLIT_PART(cleaned_string, ',', 4) AS corp_word4,
    SPLIT_PART(cleaned_string, ',', 5) AS corp_word5
    FROM raw_data.corp_keyword
)
select DISTINCT co_ke1.corpname as corpname, co_ke2.corpname as related_name
FROM co_ke1, co_ke1 AS co_ke2
WHERE co_ke1.corp_word1 = co_ke2.corp_word1
and co_ke1.corpname != co_ke2.corpname
or co_ke1.corp_word2 = co_ke2.corp_word2
and co_ke1.corpname != co_ke2.corpname
or co_ke1.corp_word3 = co_ke2.corp_word3
and co_ke1.corpname != co_ke2.corpname
or co_ke1.corp_word4 = co_ke2.corp_word4
and co_ke1.corpname != co_ke2.corpname