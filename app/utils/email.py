import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(smtp_config: dict, to_email: str, subject: str, html_body: str) -> None:
    """
    Send an email using the provided SMTP configuration.

    smtp_config keys: host, port, username, password, encryption ("TLS", "SSL", "None")
    """
    host = (smtp_config.get("host") or "").strip()
    port = int(smtp_config.get("port") or 587)
    username = (smtp_config.get("username") or "").strip()
    password = (smtp_config.get("password") or "").strip()
    encryption = (smtp_config.get("encryption") or "None").upper()

    if not host:
        raise ValueError("SMTP host no configurado en system_configuration")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "jairced.7@gmail.com"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if encryption == "SSL":
            server = smtplib.SMTP_SSL(host, port, timeout=10)
            server.ehlo()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            if encryption == "TLS":
                server.starttls()
                server.ehlo()

        if username and password:
            server.login(username, password)
        elif username or password:
            logger.warning("SMTP: usuario o contraseña vacíos, se omite autenticación")
        print(f"[SMTP] from={username!r} to={to_email!r} host={host}:{port} enc={encryption}")
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        print(f"[SMTP] Email enviado exitosamente a {to_email}")
    except Exception as exc:
        logger.error("Error al enviar email a %s: %s", to_email, exc)
        raise
