-- This sample SQL is copied from official HiveQL Documentation
-- URL: https://cwiki.apache.org/confluence/display/Hive/LanguageManual+DDL

CREATE TABLE my_table(a string, b bigint)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE;