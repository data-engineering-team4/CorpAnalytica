from airflow import DAG
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
import datetime
import logging
import os
import requests
import pandas as pd
import numpy as np
import math
import concurrent.futures
from plugins import slack_web_hook

default_args = {
    'owner': 'SeungEonKim',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': slack_web_hook.on_failure_callback,
    'on_success_callback': slack_web_hook.on_success_callback,
}

with DAG(
        dag_id='get_corp_detail_dag',
        start_date=datetime.datetime(2023, 8, 17),
        schedule_interval='0 15 * * *',
        max_active_runs=1,
        default_args=default_args,
        catchup=False
) as dag:

    api_key = Variable.get("corp_detail_api_key")
    bucket_name = "de-4-3"
    folder_name = "data/corp_detail"
    file_name = "corp_detail"
    aws_conn_id = "S3_conn"
    schema='raw_data'  # Redshift 테이블 스키마
    table='corp_detail'  # Redshift 테이블 이름
    redshift_conn_id = "Redshift_conn"

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    save_file_name = f"{file_name}_{current_date}.parquet"
    s3_key = os.path.join(folder_name, save_file_name)

    def get_corp_info(page):
        url = ("https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2?"
            f"serviceKey={api_key}&pageNo={page}&numOfRows=50000&resultType=json")

        try:
            data = requests.get(url).json()
            items = data['response']['body']['items']['item']
            return items
        except requests.exceptions.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}")
            return []

    def make_parquet():
        url = ("https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2?"
            f"serviceKey={api_key}&pageNo=1&numOfRows=1&resultType=json")

        tc_response = requests.get(url).json()
        total_count = tc_response['response']['body']['totalCount']
        loop_count = math.ceil(total_count / 50000)
        print("total_count : ", total_count)
        
        final = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_corp_info, i + 1) for i in np.arange(loop_count)]
            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                final.extend(items)
        
        df = pd.DataFrame(final)
        # csv_filename = 'data/test_gpt.csv'
        # df.to_csv(csv_filename, index=False, header=True)

        parquet_filename = f"{folder_name}/{file_name}.parquet"
        
        logging.info(parquet_filename)
        df.to_parquet(parquet_filename, engine='pyarrow', compression='gzip', index=False)

        logging.info("parquet 파일 저장 완료")


    def upload_parquet_to_s3():
        s3_hook = S3Hook(aws_conn_id = aws_conn_id)
        logging.info("Connection Success")
        
        s3_hook.load_file(
            filename = f"{folder_name}/{file_name}.parquet", # 로컬의 파일 이름
            key = s3_key, # s3에 저장되는 파일 경로 및 이름
            bucket_name = bucket_name,
            replace=True
        )
        logging.info("Upload Parquet File Success")


    # Task

    make_data_parquet_task = PythonOperator(
        task_id='make_data_parquet_task',
        python_callable= make_parquet,
        provide_context=True,
        dag=dag
    )

    upload_parquet_to_s3_task = PythonOperator(
        task_id='upload_parquet_to_s3_task',
        python_callable= upload_parquet_to_s3,
        provide_context=True,
        dag=dag
    )

    # S3에서 Redshift로 데이터를 복사하는 태스크
    s3_to_redshift_task = S3ToRedshiftOperator(
        task_id='s3_to_redshift_task',
        schema=schema,  # Redshift 테이블 스키마
        table=table,  # Redshift 테이블 이름
        copy_options=['parquet'],  # 복사 옵션 설정
        redshift_conn_id = redshift_conn_id,
        aws_conn_id = aws_conn_id,  # S3 연결 ID
        s3_bucket = bucket_name,  # S3 버킷 이름
        s3_key=s3_key,  # S3 키
        method = "REPLACE", # Full refresh 형태
        dag=dag
    )

    make_data_parquet_task >> upload_parquet_to_s3_task >> s3_to_redshift_task