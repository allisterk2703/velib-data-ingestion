import html
import logging
from urllib.parse import urlsplit

from airflow.models import Variable
from airflow.utils.email import send_email

logger = logging.getLogger(__name__)

# The webserver listens on 8090 (airflow.cfg base_url still says 8080), and
# airflow.allisterkohn.com proxies to it over HTTP for LAN and Tailscale clients.
LOCAL_BASE_URL = "http://localhost:8090"
PUBLIC_BASE_URL = "http://airflow.allisterkohn.com"
TIMEZONE = "Europe/Paris"
MAX_ERROR_CHARS = 1500

RED = "#e5484d"
TEXT = "#1c2024"
MUTED = "#60646c"
BORDER = "#e8e8ec"

# San Francisco, Apple's system font: it cannot be embedded, so it is referenced through the
# system font keywords (-apple-system for Safari and Apple Mail, BlinkMacSystemFont for Chrome).
# Non-Apple devices fall back to their own system font.
FONT = "-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue','Segoe UI',Roboto,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace"


def log_urls(log_url: str) -> tuple[str, str]:
    """Return the log link on the domain and on localhost, keeping its path and query."""
    parts = urlsplit(log_url)
    path = parts.path + (f"?{parts.query}" if parts.query else "")
    return PUBLIC_BASE_URL + path, LOCAL_BASE_URL + path


def format_date(value) -> str:
    if hasattr(value, "in_timezone"):
        return value.in_timezone(TIMEZONE).strftime("%d/%m/%Y %H:%M:%S %Z")
    return str(value)


def detail_row(label: str, value: str, mono: bool = False) -> str:
    font = f"font-family:{MONO};font-size:13px;" if mono else ""
    return (
        f'<tr><td style="padding:8px 0;color:{MUTED};font-size:14px;width:120px;'
        f'vertical-align:top;">{label}</td>'
        f'<td style="padding:8px 0;color:{TEXT};font-size:14px;{font}'
        f'word-break:break-all;">{html.escape(value)}</td></tr>'
    )


def button(url: str, label: str, primary: bool) -> str:
    style = (
        f"background:{RED};color:#ffffff;border:1px solid {RED};"
        if primary
        else f"background:#ffffff;color:{TEXT};border:1px solid {BORDER};"
    )
    return (
        f'<td style="padding:0 8px 8px 0;"><a href="{html.escape(url)}" '
        f'style="{style}font-family:{FONT};display:inline-block;padding:10px 18px;border-radius:6px;'
        f'font-size:14px;font-weight:600;text-decoration:none;">{label}</a></td>'
    )


def build_html(dag_id: str, task_id: str, run_id: str, date: str, error: str, log_url: str) -> str:
    public_url, local_url = log_urls(log_url)
    error_block = ""
    if error:
        error_block = (
            f'<p style="margin:24px 0 8px;color:{MUTED};font-size:14px;">Error</p>'
            f'<pre style="margin:0;padding:12px;background:#fff5f5;border:1px solid #fdd8d8;'
            f"border-radius:6px;color:{TEXT};font-family:{MONO};"
            f'font-size:12px;white-space:pre-wrap;word-break:break-word;">{html.escape(error)}</pre>'
        )
    return f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#f4f4f6;font-family:{FONT};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f6;">
<tr><td align="center" style="padding:32px 16px;font-family:{FONT};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border:1px solid {BORDER};border-radius:10px;border-top:4px solid {RED};">
<tr><td style="padding:28px 28px 8px;">
  <table role="presentation" cellpadding="0" cellspacing="0"><tr>
    <td width="48" height="48" align="center" valign="middle" style="width:48px;height:48px;background:{RED};border-radius:24px;color:#ffffff;font-size:26px;font-weight:700;line-height:48px;">&#10005;</td>
    <td style="padding-left:16px;">
      <div style="color:{RED};font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Task failed</div>
      <div style="color:{TEXT};font-size:20px;font-weight:700;margin-top:2px;">{html.escape(dag_id)}</div>
    </td>
  </tr></table>
</td></tr>
<tr><td style="padding:16px 28px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {BORDER};">
    {detail_row("DAG", dag_id)}
    {detail_row("Task", task_id)}
    {detail_row("Run", run_id, mono=True)}
    {detail_row("Logical date", date)}
  </table>
  {error_block}
</td></tr>
<tr><td style="padding:24px 28px 20px;">
  <p style="margin:0 0 12px;color:{MUTED};font-size:14px;">View logs</p>
  <table role="presentation" cellpadding="0" cellspacing="0"><tr>
    {button(public_url, "airflow.allisterkohn.com", primary=True)}
    {button(local_url, "localhost:8090", primary=False)}
  </tr></table>
  <p style="margin:8px 0 0;color:{MUTED};font-size:12px;">airflow.allisterkohn.com works from the LAN or Tailscale, localhost only on the Raspberry Pi.</p>
</td></tr>
</table>
<p style="margin:16px 0 0;color:{MUTED};font-size:12px;">Sent by Airflow on the Raspberry Pi 5</p>
</td></tr></table>
</body></html>"""


def notify_task_failure(context):
    try:
        emails = Variable.get("ALERT_EMAILS", deserialize_json=True)
    except Exception:
        logger.error("ALERT_EMAILS variable not found or invalid")
        return

    dag_id = context["dag"].dag_id
    task_instance = context["task_instance"]
    exception = context.get("exception")
    error = str(exception)[:MAX_ERROR_CHARS] if exception else ""
    date = context.get("logical_date") or context["execution_date"]

    subject = f"[AIRFLOW][FAILURE] {dag_id}.{task_instance.task_id}"
    html_content = build_html(
        dag_id=dag_id,
        task_id=task_instance.task_id,
        run_id=str(task_instance.run_id),
        date=format_date(date),
        error=error,
        log_url=task_instance.log_url,
    )

    send_email(
        to=emails,
        subject=subject,
        html_content=html_content,
    )
