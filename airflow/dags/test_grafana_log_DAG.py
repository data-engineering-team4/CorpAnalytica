from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from airflow.configuration import conf
import time

from statsd import StatsClient

STATSD_HOST = conf.get("metrics", "statsd_host")
STATSD_PORT = conf.get("metrics", "statsd_port")
STATSD_PREFIX = conf.get("metrics", "statsd_prefix")
client = StatsClient(host=STATSD_HOST, port=STATSD_PORT, prefix=STATSD_PREFIX)

dag = DAG(
    dag_id='HelloWorld',
    start_date=datetime(2022,5,5),
    catchup=False,
    tags=['example'],
    schedule='0 2 * * *')

def print_hello():
    print("hello!")
    return "hello!"

def for_count(**context):
    metric_name = f'dag.{context["dag"].dag_id}.{context["task"].task_id}.my_counter'

    for i in range(9):
        time.sleep(1)
        client.incr(metric_name)

def for_count_2(**context):
    metric_name = f'dag.{context["dag"].dag_id}.{context["task"].task_id}.my_counter'

    for i in range(5):
        time.sleep(1)
        in_count_func(metric_name)

def in_count_func(metric_name):
    print("in_count_func print")
    client.incr(metric_name)

print_hello = PythonOperator(
    task_id = 'print_hello',
    #python_callable param points to the function you want to run 
    python_callable = print_hello,
    #dag param points to the DAG that this task is a part of
    dag = dag)

for_count_task = PythonOperator(
    task_id = 'for_count_task',
    python_callable = for_count,
    provide_context=True,
    dag = dag
)

for_count_task_2 = PythonOperator(
    task_id = 'for_count_task_2',
    python_callable = for_count_2,
    provide_context=True,
    dag = dag
)

#Assign the order of the tasks in our DAG
print_hello >> for_count_task >> for_count_task_2
