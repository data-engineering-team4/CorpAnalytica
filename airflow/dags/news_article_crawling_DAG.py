from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.models import XCom

from datetime import datetime, timedelta
import datetime
import pendulum
import csv
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging
from plugins import slack_web_hook

local_timezone = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'Sun',
    # 'retries': 1,
    # 'retry_delay': timedelta(minutes=2),
    # 'on_failure_callback': slack_web_hook.on_failure_callback,
    # 'on_success_callback': slack_web_hook.on_success_callback,
}

with DAG(
        dag_id='news_article_crawling_DAG',
        start_date=datetime.datetime(2023, 8, 18, tzinfo=local_timezone),
        max_active_runs=1,
        default_args=default_args,
        catchup=False
) as dag:
    
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1)
    session.mount('https://', HTTPAdapter(max_retries=retry))
    session.mount('http://', HTTPAdapter(max_retries=retry))
    
    
    # Function


    # 네이버 뉴스 csv 파일로부터 링크를 읽어서 뉴스 데이터 크롤링
    def get_news_article_crawling_data_from_naver_news(**kwargs):

        logical_date_kst = kwargs['logical_date'] + timedelta(hours=9)
        logging.info(f"-- logical_date : {logical_date_kst} --\n-- 해당 날짜에서 뉴스 데이터를 가져옵니다. --")

        naver_news_csv_filename = "data/naver_news/naver_news_" + str(logical_date_kst.date()) + ".csv"
        news_article_parquet_filename = "data/news_article/news_article_" + str(logical_date_kst.date()) + ".parquet"
        kwargs['ti'].xcom_push(key='news_article_parquet_filename', value=news_article_parquet_filename)

        with open(naver_news_csv_filename, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader) # 헤더 무시

            total_news_article_list = []
            for line in csv_reader:
                corpname = line[1]
                link = line[3]
                article = news_crawling_from_link(link)

                # 뉴스 기사 데이터를 가져오지 못했으면 다음으로 스킵
                if len(article) < 1:
                    logging.info(f"{corpname}의 뉴스 데이터를 가져올 수 없습니다. 링크 : {link}")
                    continue
                
                news_dic = {
                    'corpname' : corpname,
                    'link' : link,
                    'article' : article,
                }
                total_news_article_list.append(news_dic)

                logging.info(f"{len(total_news_article_list)} : {corpname}의 뉴스 {line[2]} 저장")
            
            df = pd.DataFrame(total_news_article_list)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, news_article_parquet_filename)
            # df.to_csv(news_article_csv_filename, index=False, encoding='utf-8')

    # s3에 parquet 파일 업로드
    def upload_parquet_to_s3(**kwargs):
        s3_hook = S3Hook(aws_conn_id='S3_conn')
        logging.info("S3 Connection Success")

        news_article_parquet_filename = kwargs['ti'].xcom_pull(task_ids='get_news_article_crawling_parquet_task', key='news_article_parquet_filename')
        
        s3_hook.load_file(
            filename=news_article_parquet_filename, 
            key=news_article_parquet_filename,
            bucket_name="de-4-3",
            replace=True
            )
        logging.info("Upload Parquet File Success")

    # 네이버 뉴스 크롤링
    def news_crawling_from_link(link):
        article = ""

        try:
            response = session.get(link)
            soup = BeautifulSoup(response.text, "html.parser")

            if response.status_code != 200:
                return ""
            
            if "n.news.naver.com" in link:
                article_tag = soup.find("article")

            elif "www.enetnews.co.kr" in link:               
                article_tag = soup.find("article", id = "article-view-content-div")

            elif "www.itooza.com" in link:
                extract_tag = soup.find(class_="btn-wrap-01")
                extract_tag.extract()

                article_tag = soup.find("div", id = "article-body")

            elif "www.ggilbo.com" in link:
                article_tag = soup.find("article", id = "article-view-content-div")

            elif "www.cbci.co.kr" in link:
                # 제외할 태그들의 클래스 리스트
                exclude_classes = ['view-editors', 'view-copyright', 'figcaption']

                # 제외할 태그들을 반복문으로 제거
                for class_name in exclude_classes:
                    extract_tags = soup.find_all(class_=class_name)
                    
                    for extract_tag in extract_tags:
                        extract_tag.extract()

                article_tag = soup.find("div", id = "article-view-content-div")
                
                # 끝의 두 개 p 태그 제거
                article_tag_p_extract = article_tag.find_all('p')

                if len(article_tag_p_extract) >= 2:
                    article_tag_p_extract[-1].extract()
                    article_tag_p_extract[-2].extract()

            elif "sports.news.naver.com" in link:
                # 제외할 태그들의 클래스 리스트
                exclude_classes = ['source', 'byline', 'reporter_area', 'copyright', 'categorize', 'promotion' ]

                # 제외할 태그들을 반복문으로 제거
                for class_name in exclude_classes:
                    extract_tags = soup.find_all(class_=class_name)
                    
                    for extract_tag in extract_tags:
                        extract_tag.extract()

                article_tag = soup.find("div", id = "newsEndContents")

            elif "www.lcnews.co.kr" in link:
                article_tag = soup.find("article", id = "article-view-content-div")

            elif "www.wsobi.com" in link:
                # 인코딩 필요, 나중에 다른 언론사와 병합해도 되는지 확인필요함
                response = session.get(link)
                response.encoding = 'cp949'  
                soup = BeautifulSoup(response.text, "html.parser")

                article_tag = soup.find("div", id = "articleBody")

                article_tag_p_extract = article_tag.find_all('p')

                if len(article_tag_p_extract) >= 2:
                    article_tag_p_extract[-1].extract()
                    article_tag_p_extract[-2].extract()

            elif "www.gukjenews.com" in link:
                # 이미지 출처 제거
                extract_tags = soup.find_all('figcaption')
                for extract_tag in extract_tags:
                    extract_tag.extract()

                article_tag = soup.find("article", id = "article-view-content-div")

            elif "www.thebell.co.kr" in link:
                extract_tag = soup.find(class_="tip mgb20")
                extract_tag.extract()

                article_tag = soup.find("div", id = "article_main")

            elif "https://www.etoday.co.kr" in link:
                extract_tag = soup.find('div', class_='relation_newslist')
                extract_tag.extract()
                
                article_tag = soup.select_one('.articleView')

            elif "www.newspim.com" in link:
                article_tag = soup.find('div', id='news-contents')

            elif "www.thekpm.com" in link:
                article_tag = soup.find('article', id='article-view-content-div')

            elif "news.mtn.co.kr" in link:
                extract_tag = soup.find('table', class_='article-photo-news center')
                extract_tag.extract()

                article_tag = soup.select_one('.news-content')

            elif "www.pinpointnews.co.kr" in link:
                article_tag = soup.find('article', id='article-view-content-div')

            elif "http://www.econonews.co.kr/" in link:
                article_tag = soup.find('article', id='article-view-content-div')

            elif "www.news2day.co.kr" in link:
                extract_tag = soup.find('figure', id='id_div_main')
                extract_tag.extract()

                article_tag = soup.select_one('.view_con.cf') 

            elif "http://www.thebigdata.co.kr/" in link:
                article_tag = soup.find('div', class_='txt_article')

            else:
                return ""

            article = article_tag.text

        except requests.exceptions.RequestException as e:
            logging.info(e)
            logging.info(f"Request Failed / 링크 : {link}")

        except AttributeError as e:
            logging.error(f"{link}에는 해당 태그를 찾을 수 없습니다. / {e}")
        
        except Exception as e:
            logging.error(f"기타 에러 / 링크 : {link} / 에러 : {e}")

        article = article.replace('\n', '').replace('\r', '').replace('\t', '').strip()    
        return article


    # Task


    get_news_article_crawling_parquet_task = PythonOperator(
        task_id='get_news_article_crawling_parquet_task',
        python_callable= get_news_article_crawling_data_from_naver_news,
        provide_context=True,
        dag=dag
    )

    upload_news_article_parquet_to_s3_task = PythonOperator(
        task_id='upload_news_article_parquet_to_s3_task',
        python_callable= upload_parquet_to_s3,
        provide_context=True,
        dag=dag
    )

    news_article_crawling_s3_to_redshift_task = S3ToRedshiftOperator(
        task_id = 'news_article_crawling_s3_to_redshift_task',
        s3_bucket = "de-4-3",
        s3_key = "{{ ti.xcom_pull(task_ids='get_news_article_crawling_parquet_task', key='news_article_parquet_filename') }}",
        schema = "raw_data",
        table = "news_article",
        copy_options=['parquet'],
        redshift_conn_id = "redshift_conn",
        aws_conn_id = "S3_conn",    

        method = "UPSERT",
        upsert_keys = ["link"],
        dag = dag
    )

    get_news_article_crawling_parquet_task >> upload_news_article_parquet_to_s3_task >> news_article_crawling_s3_to_redshift_task