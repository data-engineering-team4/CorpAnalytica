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

def query_redshift_to_dataframe():
    redshift_conn_id = 'Redshift_conn'  # Airflow Connection ID for Redshift
    logical_date_utc = datetime.now()
    logical_date_kst = (logical_date_utc + timedelta(hours=9) - timedelta(days=1)).strftime("%Y-%m-%d")
    logging.info(logical_date_kst)
    #sql_query = f"select ne.keyword from raw_data.news_keyword ne, raw_data.naver_news na where ne.corpname = na.corpname and na.pubdate like '{str(logical_date_kst)}%';"
    sql_query1 = f"""select REPLACE(REPLACE(REPLACE(ne.keyword, '[', ''), ']', ''), '''', '') AS cleaned_string
                from raw_data.news_keyword ne, raw_data.naver_news na where ne.id = na.id and na.pubdate like '{str(logical_date_kst)}%';"""
    sql_query2 = f"""select corpname from raw_data.naver_news where pubdate like '{str(logical_date_kst)}%';"""

    redshift_hook = PostgresHook(redshift_conn_id)
    connection = redshift_hook.get_conn()
    logging.info("redshift Connection Success")

    df1 = pd.read_sql_query(sql_query1, connection)
    logging.info("news_keyword extract")
    logging.info(df1[:10])

    df2 = pd.read_sql_query(sql_query2, connection)
    logging.info("corpnames extract")
    logging.info(df2[:10])

    connection.close()
    return df1, df2


def create_wordcloud(**kwargs):
    keywords, corps = query_redshift_to_dataframe()

    combined_keywords = ','.join(keywords['cleaned_string'])
    keywords_list = combined_keywords.split(',')
    keywords_count = dict(sorted(Counter(keywords_list).items(), key=lambda x: x[1], reverse=True)[:30])

    combined_corps = ','.join(corps['corpname'])
    corps_list = combined_corps.split(',')
    corps_count = dict(sorted(Counter(corps_list).items(), key=lambda x: x[1], reverse=True)[:15])
    logging.info("Wordcount Success")

    font_path = 'data/BMDOHYEON_ttf.ttf'  # 다운로드한 한글 폰트 파일 경로
    
    wordcloud_keywords = WordCloud(width=800, height=800, 
                        font_path=font_path, 
                        background_color='gray', 
                        colormap = 'autumn').generate_from_frequencies(keywords_count)
    
    wordcloud_corps = WordCloud(width=800, height=800, 
                        font_path=font_path, 
                        background_color='gray', 
                        colormap = 'spring').generate_from_frequencies(corps_count)
    
    logical_date_kst = kwargs['logical_date'] + timedelta(hours=9)

    news_wordcloud_png_filename = "data/news_wordcloud/news_wordcloud_" + str(logical_date_kst.date()) + ".png"
    corp_wordcloud_png_filename = "data/news_wordcloud/corp_wordcloud_" + str(logical_date_kst.date()) + ".png"    

    wordcloud_keywords.to_file(news_wordcloud_png_filename)
    kwargs['ti'].xcom_push(key='news_wordcloud_png_filename', value=news_wordcloud_png_filename)

    wordcloud_corps.to_file(corp_wordcloud_png_filename)
    kwargs['ti'].xcom_push(key='corp_wordcloud_png_filename', value=corp_wordcloud_png_filename)

    logging.info("Wordcloud Success")

def upload_to_s3(**kwargs):
    s3_hook = S3Hook(aws_conn_id='S3_conn')
    logging.info("S3 Connection Success")
    
    news_wordcloud_png_filename = kwargs['ti'].xcom_pull(task_ids='create_wordcloud', key='news_wordcloud_png_filename')
    corp_wordcloud_png_filename = kwargs['ti'].xcom_pull(task_ids='create_wordcloud', key='corp_wordcloud_png_filename')

    s3_hook.load_file(
        filename=news_wordcloud_png_filename, 
        key=news_wordcloud_png_filename,
        bucket_name="de-4-3",
        replace=True
    )
    logging.info("load_news_wordcloud_file")

    s3_hook.load_file(
        filename=corp_wordcloud_png_filename, 
        key=corp_wordcloud_png_filename,
        bucket_name="de-4-3",
        replace=True
    )
    logging.info("load_corp_wordcloud_file")

with DAG('wordcloud_dag', 
        default_args=default_args, 
        schedule_interval=None, 
        catchup=False) as dag:

    create_wordcloud_task = PythonOperator(
        task_id='create_wordcloud',
        python_callable=create_wordcloud,
        provide_context=True,
        dag = dag
    )

    upload_to_s3_task = PythonOperator(
        task_id='upload_to_s3',
        python_callable=upload_to_s3,
        provide_context=True,
        dag=dag
    )

    create_wordcloud_task >> upload_to_s3_task
