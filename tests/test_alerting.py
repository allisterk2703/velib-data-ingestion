import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path.home() / "airflow" / "plugins"))

sys.modules.setdefault("airflow", MagicMock())
sys.modules.setdefault("airflow.models", MagicMock())
sys.modules.setdefault("airflow.utils", MagicMock())
sys.modules.setdefault("airflow.utils.email", MagicMock())

from callbacks.notify import notify_task_failure  # noqa: E402


def _make_context(dag_id="test_dag", task_id="test_task"):
    dag = MagicMock()
    dag.dag_id = dag_id
    task_instance = MagicMock()
    task_instance.task_id = task_id
    task_instance.log_url = "http://localhost/log"
    return {
        "dag": dag,
        "task_instance": task_instance,
        "execution_date": "2026-01-01T00:00:00",
    }


def test_notify_task_failure_sends_email():
    context = _make_context()

    with (
        patch("callbacks.notify.Variable.get", return_value=["test@example.com"]),
        patch("callbacks.notify.send_email") as mock_send,
    ):
        notify_task_failure(context)

    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args
    assert "test_dag" in call_kwargs.kwargs.get("subject", "") or "test_dag" in str(call_kwargs)


def test_notify_task_failure_subject_format():
    context = _make_context(dag_id="my_dag", task_id="my_task")

    with (
        patch("callbacks.notify.Variable.get", return_value=["a@b.com"]),
        patch("callbacks.notify.send_email") as mock_send,
    ):
        notify_task_failure(context)

    subject = mock_send.call_args.kwargs["subject"]
    assert subject == "[AIRFLOW][FAILURE] my_dag.my_task"
