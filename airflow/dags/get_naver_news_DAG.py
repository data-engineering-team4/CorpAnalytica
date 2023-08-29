from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from airflow.models import XCom
from airflow.configuration import conf

from datetime import datetime, timedelta
import pendulum
import time
import pandas as pd
import csv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from statsd import StatsClient
from plugins import slack_web_hook


local_timezone = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'Sun',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': slack_web_hook.on_failure_callback,
    # 'on_success_callback': slack_web_hook.on_success_callback,
}

with DAG(
        dag_id='get_naver_news_DAG',
        start_date=datetime(2023, 8, 17, tzinfo=local_timezone),
        max_active_runs=1,
        default_args=default_args,
        catchup=False
) as dag:
    
    session = requests.Session()
    retry = Retry(total= 3, connect=3, backoff_factor=0.3)
    session.mount('https://', HTTPAdapter(max_retries=retry))

    STATSD_HOST = conf.get("metrics", "statsd_host")
    STATSD_PORT = conf.get("metrics", "statsd_port")
    STATSD_PREFIX = conf.get("metrics", "statsd_prefix")
    client = StatsClient(host=STATSD_HOST, port=STATSD_PORT, prefix=STATSD_PREFIX)


    # Function
    

    # 네이버 뉴스 API로부터 해당 기업의 뉴스 데이터 가져오기
    def get_news_data_from_naver_searchAPI(corpname, stock_code, logical_date_kst, metric_name):

        params = {
            "query": corpname,
            "display": 100,
            "sort": "date",
            "start": 1,
        }

        url = "https://openapi.naver.com/v1/search/news"

        headers = {
            "X-Naver-Client-Id": Variable.get("naver_client_id"),
            "X-Naver-Client-Secret": Variable.get("naver_client_secret")
        }

        try:
            news_data_response = session.get(url, params=params, headers=headers).json()

            # 가져온 뉴스 데이터를 리스트(사전배열) 형태로 저장 > 나중에 DataFrame으로 만들기 위함  
            corp_news_data_list = []
            for news in news_data_response["items"]:
                pubdate = news['pubDate']
                pubdate_parsed = datetime.strptime(pubdate, '%a, %d %b %Y %H:%M:%S %z')
                formatted_pubdate = pubdate_parsed.strftime("%Y-%m-%d %H:%M:%S")

                if pubdate_parsed.date() == logical_date_kst.date():

                    # 'code' 부분 수정해야함
                    news_data_dic = {
                        'id' : corpname + ' ' + news['link'],
                        'code' : stock_code,
                        'corpname' : corpname,
                        'title' : news['title'],
                        'link' : news['link'],
                        'description' : news['description'],
                        'pubDate' : formatted_pubdate
                    }
                    
                    corp_news_data_list.append(news_data_dic)
                    client.incr(metric_name)

            return corp_news_data_list
        
        except requests.exceptions.RequestException as e:
            logging.info(e)
            logging.info(f"Request Failed / 기업 이름 : {corpname}")

            return []


    # 상장 기업목록들을 가져와서 모든 뉴스 데이터를 리스트에 저장
    def make_corps_news_list(logical_date_kst, metric_name):

        with open("data/corp_basic/corp_basic.csv", 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader) # 헤더 무시

            # 가져온 기업들의 뉴스 데이터를 모두 total_corp_news_data_list에 합쳐서 저장
            total_corp_news_data_list = []
            for i, line in enumerate(csv_reader):
                corpname = line[1]
                stock_code = line[2]
                corp_news_data_list = get_news_data_from_naver_searchAPI(corpname, stock_code, logical_date_kst, metric_name)
                total_corp_news_data_list += corp_news_data_list
                logging.info(f"{i} : {corpname}의 뉴스 데이터 {len(corp_news_data_list)}개 저장")
                time.sleep(0.11) # 네이버 API 제한량 때문

        return total_corp_news_data_list


    # 가져온 뉴스 데이터들을 CSV 파일로 저장
    def get_naver_news_csv(**kwargs):

        metric_name = f'dag.{kwargs["dag"].dag_id}.{kwargs["task"].task_id}.news_counter'

        logical_date_kst = kwargs['logical_date'] + timedelta(hours=9)

        logging.info(f"---logical_date_KST = {logical_date_kst}---")
        logging.info(f"---뉴스 데이터를 해당 날짜에서 수집합니다.---")

        news_data_list = make_corps_news_list(logical_date_kst, metric_name)

        # csv 파일 생성
        csv_filename = "data/naver_news/naver_news_" + str(logical_date_kst.date()) + ".csv"
        kwargs['ti'].xcom_push(key='csv_filename', value=csv_filename)

        columns = ['id','code','corpname','title','link','description', 'pubDate']
        df = pd.DataFrame.from_records(news_data_list, columns=columns)  # 데이터프레임 생성

        df.to_csv(csv_filename, index=False, encoding='utf-8') # CSV 파일로 저장
        logging.info("csv 파일 저장 완료")


    # 저장된 CSV 파일을 S3에 저장
    def upload_csv_to_s3(**kwargs):
        s3_hook = S3Hook(aws_conn_id='S3_conn')
        logging.info("Connection Success")
        csv_filename = kwargs['ti'].xcom_pull(task_ids='make_news_data_csv_task', key='csv_filename')
        
        s3_hook.load_file(
            filename=csv_filename, 
            key=csv_filename, 
            bucket_name="de-4-3",
            replace=True
            )
        logging.info("Upload CSV File Success")


    # Task


    make_news_data_csv_task = PythonOperator(
        task_id='make_news_data_csv_task',
        python_callable= get_naver_news_csv,
        provide_context=True,
        dag=dag
    )

    upload_naver_news_csv_to_s3_task = PythonOperator(
        task_id='upload_csv_to_s3_task',
        python_callable= upload_csv_to_s3,
        provide_context=True,
        dag=dag
    )

    news_data_s3_to_redshift_task = S3ToRedshiftOperator(
        task_id = 'news_data_s3_to_redshift_task',
        s3_bucket = "de-4-3",
        s3_key = "{{ ti.xcom_pull(task_ids='make_news_data_csv_task', key='csv_filename') }}",
        schema = "raw_data",
        table = "naver_news",
        copy_options=["csv", "IGNOREHEADER 1"],
        redshift_conn_id = "Redshift_conn",
        aws_conn_id = "S3_conn",    

        method = "UPSERT",
        upsert_keys = ["id"],
        dag = dag
    )

    trigger_get_news_article_task = TriggerDagRunOperator(
        task_id='trigger_get_news_article_task',
        trigger_dag_id='news_article_crawling_DAG',
        execution_date="{{ execution_date }}"
    )

    make_news_data_csv_task >> upload_naver_news_csv_to_s3_task >> news_data_s3_to_redshift_task >> trigger_get_news_article_task
