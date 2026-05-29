import logging

from airflow.models import Variable
from airflow.utils.email import send_email

logger = logging.getLogger(__name__)


def notify_task_failure(context):
    try:
        emails = Variable.get("ALERT_EMAILS", deserialize_json=True)
    except Exception:
        logger.error("ALERT_EMAILS variable not found or invalid")
        return

    dag_id = context["dag"].dag_id
    task_instance = context["task_instance"]

    subject = f"[AIRFLOW][FAILURE] {dag_id}.{task_instance.task_id}"

    html_content = f"""
    <h3>Airflow task failed</h3>
    <ul>
        <li>DAG: {dag_id}</li>
        <li>Task: {task_instance.task_id}</li>
        <li>Execution date: {context["execution_date"]}</li>
        <li><a href="{task_instance.log_url}">View logs</a></li>
    </ul>
    """

    send_email(
        to=emails,
        subject=subject,
        html_content=html_content,
    )
