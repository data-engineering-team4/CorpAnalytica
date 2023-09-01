from datetime import datetime, timedelta
import datetime
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
#from plugins import slack

default_args = {
    'owner': 'analytics',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    #'on_failure_callback': slack.on_failure_callback
}

with DAG(
    dag_id = 'get_analytics',
    start_date=datetime.datetime(2023,8,29),
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args=default_args, 
    catchup=False
) as dag:

    get_analytics = BashOperator(
        task_id='get_analytics',
        bash_command='cd /dbt/CorpAnalytica_dbt && dbt run --profiles-dir .',
        env={
            'dbt_user': '{{ var.value.dbt_redshift_user }}',
            'dbt_password': '{{ var.value.dbt_redshift_password }}',
            **os.environ
        },
        dag=dag
    )

get_analytics