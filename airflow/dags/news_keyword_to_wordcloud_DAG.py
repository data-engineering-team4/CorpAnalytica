import os
import requests
from airflow.models import XCom
from wordcloud import WordCloud
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import numpy as np
from collections import Counter
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import logging
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 8, 10),
    'depends_on_past': False,
    'retries': 1,
}

def query_redshift_to_dataframe(**kwargs):
    redshift_conn_id = 'Redshift_conn'  # Airflow Connection ID for Redshift
    #logical_date_kst = kwargs['logical_date'] + timedelta(hours=9)
    
    #sql_query = f"select ne.keyword from raw_data.news_keyword ne, raw_data.naver_news na where ne.corpname = na.corpname and na.pubdate like '{str(logical_date_kst)}%';"
    sql_query = """select REPLACE(REPLACE(REPLACE(ne.keyword, '[', ''), ']', ''), '''', '') AS cleaned_string 
                from raw_data.news_keyword ne, raw_data.naver_news na where ne.id = na.id and na.pubdate like '2023-08-07%';"""

    redshift_hook = PostgresHook(redshift_conn_id)
    connection = redshift_hook.get_conn()
    df = pd.read_sql_query(sql_query, connection)
    connection.close()
    logging.info("redshift Connection Success")
    logging.info(df[:10])
    return df


def create_wordcloud(**kwargs):
    keywords = query_redshift_to_dataframe()
    combined_string = ','.join(keywords['cleaned_string'])
    word_list = combined_string.split(', ')
    word_count = dict(sorted(Counter(word_list).items(), key=lambda x: x[1], reverse=True)[:30])
    logging.info("Wordcount Success")

    font_path = 'data/BMJUA.ttf'  # 다운로드한 한글 폰트 파일 경로
    
    wordcloud = WordCloud(width=800, height=800, 
                        font_path=font_path, 
                        background_color='gray', 
                        colormap = 'autumn').generate_from_frequencies(word_count)
    logical_date_kst = kwargs['logical_date'] + timedelta(hours=9)

    news_wordcloud_png_filename = "data/news_wordcloud/news_wordcloud_" + str(logical_date_kst.date()) + ".png"
    wordcloud.to_file(news_wordcloud_png_filename)
    kwargs['ti'].xcom_push(key='news_wordcloud_png_filename', value=news_wordcloud_png_filename)
    logging.info("Wordcloud Success")

def upload_to_s3(**kwargs):
    s3_hook = S3Hook(aws_conn_id='S3_conn')
    logging.info("S3 Connection Success")
    
    news_wordcloud_png_filename = kwargs['ti'].xcom_pull(task_ids='create_wordcloud', key='news_wordcloud_png_filename')

    s3_hook.load_file(
        filename=news_wordcloud_png_filename, 
        key=news_wordcloud_png_filename,
        bucket_name="de-4-3",
        replace=True
    )
    logging.info("load_file")

with DAG('wordcloud_dag', 
        default_args=default_args, 
        schedule_interval=None, 
        catchup=False) as dag:

    create_wordcloud_task = PythonOperator(
        task_id='create_wordcloud',
        python_callable=create_wordcloud
    )

    upload_to_s3_task = PythonOperator(
        task_id='upload_to_s3',
        python_callable=upload_to_s3
    )

    create_wordcloud_task >> upload_to_s3_task
