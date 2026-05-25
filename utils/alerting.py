import logging

from airflow.models import Variable
from airflow.utils.email import send_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def notify_task_failure(context):
    emails = Variable.get(
        "ALERT_EMAILS",
        deserialize_json=True,
    )

    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    execution_date = context["execution_date"]
    log_url = context["task_instance"].log_url

    subject = f"[AIRFLOW][FAILURE] {dag_id}.{task_id}"

    html_content = f"""
    <h3>Airflow task failed</h3>
    <ul>
        <li>DAG: {dag_id}</li>
        <li>Task: {task_id}</li>
        <li>Execution date: {execution_date}</li>
        <li><a href="{log_url}">View logs</a></li>
    </ul>
    """

    send_email(
        to=emails,
        subject=subject,
        html_content=html_content,
    )
