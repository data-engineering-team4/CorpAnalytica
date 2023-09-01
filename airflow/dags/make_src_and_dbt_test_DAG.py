from datetime import datetime, timedelta
import datetime
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from plugins import slack_web_hook

default_args = {
    'owner': 'analytics',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': slack_web_hook.on_failure_callback
}

with DAG(
    dag_id = 'make_src_and_dbt_test_DAG',
    start_date=datetime.datetime(2023,8,29),
    max_active_runs=1,
    default_args=default_args, 
    catchup=False
) as dag:

    make_src = BashOperator(
        task_id='make_src',
        bash_command='cd /dbt/CorpAnalytica_dbt && dbt run --profiles-dir . --model src',
        env={
            'dbt_user': '{{ var.value.dbt_redshift_user }}',
            'dbt_password': '{{ var.value.dbt_redshift_password }}',
            **os.environ
        },
        dag=dag
    )

    do_dbt_test = BashOperator(
        task_id='do_dbt_test',
        bash_command='cd /dbt/CorpAnalytica_dbt && dbt test --profiles-dir .',
        env={
            'dbt_user': '{{ var.value.dbt_redshift_user }}',
            'dbt_password': '{{ var.value.dbt_redshift_password }}',
            **os.environ
        },
        dag=dag
    )

    trigger_get_analytics = TriggerDagRunOperator(
        task_id='trigger_get_analytics',
        trigger_dag_id='get_analytics',
        execution_date="{{ execution_date }}"
    )

make_src >> do_dbt_test >> trigger_get_analytics