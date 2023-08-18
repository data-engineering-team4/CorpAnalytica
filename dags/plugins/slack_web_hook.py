from airflow.models import Variable
import requests

# dag 실패시 호출
def on_failure_callback(context):

    dag = context.get('task_instance').dag_id
    task = context.get('task_instance').task_id
    exec_date = context.get('execution_time')
    exception = context.get('exception')
    log_url = context.get('task_instance').log_url

    message = f"""
        :warning: *Task Failed.*
        - *Dag*: {dag}
        - *Task*: {task}
        - *Execution Time*: {exec_date}
        - *Exception* : {exception}
        - *Log Url* : {log_url}\n
        """

    send_message_to_a_slack_channel(message)


# def on_success_callback(context):
# 
#     dag = context.get('task_instance').dag_id
#     task = context.get('task_instance').task_id
# 
#     message = f"""
#         :large_blue_circle: *Task Successed.*
#         - *Dag*: {dag}
#         - *Task*: {task}
#     """
#     message += "\n 성공입니다! :hamster:\n"
# 
#     send_message_to_a_slack_channel(message)


# slack에 알림 보내기
def send_message_to_a_slack_channel(message):
    slack_url = Variable.get("slack_url")
    # url = f"https://hooks.slack.com/services/{slack_url}" # CorpAnalytica Alert

    url = "https://hooks.slack.com/services/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" # Test Alert
    headers = {
        'content-type': 'application/json',
    }
    data = {"text": message }
    r = requests.post(url, json=data, headers=headers)
    return r