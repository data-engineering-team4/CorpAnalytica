from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.models import Variable
# from airflow.models import XCom

from datetime import datetime, timedelta
import datetime
import pendulum
import time
import csv
import xml.etree.ElementTree as ET
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
        dag_id='get_corp_basic_DAG',
        start_date=datetime.datetime(2023, 8, 18, tzinfo=local_timezone),
        schedule_interval="0 0 * * *",
        max_active_runs=1,
        default_args=default_args,
        catchup=False
) as dag:

    session = requests.Session()
    retry = Retry(total= 3, connect=3, backoff_factor=0.3)
    session.mount('https://', HTTPAdapter(max_retries=retry))

    csv_filename = "data/corp_basic/corp_basic.csv"
    corp_exception_list = ["아스팩오일"]
    dart_api_key = Variable.get("dart_api_key")

    # Function

    # Dart API에서 데이터 가져오기
    def get_corp_basic_data_from_xml():
        xml_path = "data/CORPCODE.xml" # Dart API로부터 가져온 xml 파일

        with open(xml_path, encoding='utf-8') as corcode_xml_file :
            parsed_corcode = ET.parse(corcode_xml_file)
            corcode_root = parsed_corcode.getroot()

            with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                
                # CSV 헤더 작성
                # 순서대로 기업고유번호, 기업명, 기업종목번호, 법인등록번호
                csv_writer.writerow(['entno', 'corpname', 'code', 'crno'])

                # stock_code(종목코드)가 있는 항목만 레코드로 csv 파일 생성
                for item in corcode_root.iter("list"):
                    entno = item.find('corp_code').text # 기업고유번호
                    corpname = item.find('corp_name').text # 기업명
                    stock_code = item.find('stock_code').text # 기업종목번호

                    
                    # 주식 종목 코드가 존재하고, 기업명에 특정 문자가 없는 기업들로만 데이터 수집
                    if len(stock_code) > 1:
                        if ('기업인수' not in corpname and '스팩' not in corpname) or corpname in corp_exception_list:

                            try: 
                                url = f"https://opendart.fss.or.kr/api/company.json?crtfc_key={dart_api_key}&corp_code={entno}"
                                response = session.get(url)
                                crno = response.json()["jurir_no"] # 법인등록번호

                                csv_writer.writerow([entno, corpname, stock_code, crno])
                                logging.info(f"Add to CSV : {corpname}")

                            except requests.exceptions.RequestException as e:
                                logging.info(e)
                                logging.info(f"Request Failed / 기업 이름 : {corpname}")
                            
                            time.sleep(0.1)


        logging.info("csv 파일 생성이 완료되었습니다.")


    def upload_csv_to_s3():
        s3_hook = S3Hook(aws_conn_id='S3_conn')
        logging.info("S3 Connection Success")
        
        s3_hook.load_file(
            filename=csv_filename, 
            key=csv_filename,
            bucket_name="de-4-3",
            replace=True
            )
        logging.info("Upload CSV File Success")


    # Task


    get_corp_basic_csv_from_xml_task = PythonOperator(
        task_id='get_corp_basic_csv_from_xml_task',
        python_callable= get_corp_basic_data_from_xml,
        provide_context=True,
        dag=dag
    )

    upload_corp_basic_csv_to_s3_task = PythonOperator(
        task_id='upload_corp_basic_csv_to_s3_task',
        python_callable= upload_csv_to_s3,
        provide_context=True,
        dag=dag
    )

    corp_basic_s3_to_redshift_task = S3ToRedshiftOperator(
        task_id = 'corp_basic_s3_to_redshift_task',
        s3_bucket = "de-4-3",
        s3_key = csv_filename,
        schema = "raw_data",
        table = "corp_basic",
        copy_options=['csv', 'IGNOREHEADER 1'],
        method = 'REPLACE', # Full Refresh
        redshift_conn_id = "redshift_conn",
        aws_conn_id = "S3_conn",
        dag = dag
    )

    trigger_get_naver_news_task = TriggerDagRunOperator(
        task_id='trigger_get_naver_news_task',
        trigger_dag_id='get_naver_news_DAG',
        execution_date="{{ execution_date }}"
    )

    get_corp_basic_csv_from_xml_task >> upload_corp_basic_csv_to_s3_task >> corp_basic_s3_to_redshift_task >> trigger_get_naver_news_task