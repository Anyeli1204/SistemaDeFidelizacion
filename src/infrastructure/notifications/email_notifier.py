import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from application.ports import NotificadorRecompensa

DEFAULT_LOG = Path(os.getenv("NOTIFICATION_LOG_PATH", "data/emails_enviados.log"))


def _correo_cliente(numero_tarjeta: str) -> str:
    dominio = os.getenv("NOTIFICATION_EMAIL_DOMAIN", "fidelizacion.lab")
    sufijo = numero_tarjeta[-4:]
    return f"cliente.{sufijo}@{dominio}"


def _destinatarios(numero_tarjeta: str, email_cliente: str | None) -> list[str]:
    if email_cliente:
        return [email_cliente]
    override = os.getenv("EMAIL_TO_OVERRIDE", "").strip()
    if override:
        return [x.strip() for x in override.split(",") if x.strip()]
    return [_correo_cliente(numero_tarjeta)]


def _formatear_fecha(procesado_en: datetime) -> str:
    return procesado_en.strftime("%d/%m/%Y %H:%M UTC")


def _cuerpo_texto(
    numero_tarjeta: str,
    puntos_abonados: int,
    saldo_total: int,
    procesado_en: datetime,
) -> str:
    tarjeta = f"****{numero_tarjeta[-4:]}"
    return (
        "Programa de fidelización — recompensa procesada\n\n"
        f"Estimado cliente (tarjeta {tarjeta}),\n\n"
        f"Se abonaron {puntos_abonados} puntos a su cuenta.\n"
        f"Saldo actual: {saldo_total} puntos.\n\n"
        f"Fecha de procesamiento: {_formatear_fecha(procesado_en)}\n\n"
        "Gracias por su preferencia."
    )


def _cuerpo_html(
    numero_tarjeta: str,
    puntos_abonados: int,
    saldo_total: int,
    procesado_en: datetime,
) -> str:
    tarjeta = f"****{numero_tarjeta[-4:]}"
    fecha = _formatear_fecha(procesado_en)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Recompensa procesada</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Segoe UI,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f6f8;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="max-width:520px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:28px 32px;">
              <p style="margin:0;font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#bfdbfe;">
                Programa de fidelización
              </p>
              <h1 style="margin:8px 0 0;font-size:24px;font-weight:600;color:#ffffff;line-height:1.3;">
                ¡Puntos abonados!
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#334155;">
                Estimado cliente, su consumo fue procesado correctamente.
              </p>
              <p style="margin:0 0 24px;font-size:14px;color:#64748b;">
                Tarjeta <strong style="color:#1e293b;">{tarjeta}</strong>
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:24px;">
                <tr>
                  <td width="50%" style="padding-right:8px;vertical-align:top;">
                    <div style="background:#ecfdf5;border-radius:10px;padding:20px;text-align:center;border:1px solid #a7f3d0;">
                      <p style="margin:0;font-size:12px;color:#047857;text-transform:uppercase;letter-spacing:0.05em;">
                        Puntos abonados
                      </p>
                      <p style="margin:8px 0 0;font-size:32px;font-weight:700;color:#059669;line-height:1;">
                        +{puntos_abonados}
                      </p>
                    </div>
                  </td>
                  <td width="50%" style="padding-left:8px;vertical-align:top;">
                    <div style="background:#eff6ff;border-radius:10px;padding:20px;text-align:center;border:1px solid #bfdbfe;">
                      <p style="margin:0;font-size:12px;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.05em;">
                        Saldo actual
                      </p>
                      <p style="margin:8px 0 0;font-size:32px;font-weight:700;color:#2563eb;line-height:1;">
                        {saldo_total}
                      </p>
                    </div>
                  </td>
                </tr>
              </table>
              <p style="margin:0;font-size:13px;color:#94a3b8;text-align:center;">
                Procesado el {fecha}
              </p>
            </td>
          </tr>
          <tr>
            <td style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:13px;color:#64748b;text-align:center;line-height:1.5;">
                Gracias por su preferencia.<br>
                <span style="color:#94a3b8;">Laboratorio 8 -CS3081 — Fidelización en restaurantes</span>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _crear_mensaje_smtp(
    destinos: list[str],
    asunto: str,
    texto: str,
    html: str,
    remitente: str,
) -> MIMEMultipart:
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = ", ".join(destinos)
    mensaje.attach(MIMEText(texto, "plain", "utf-8"))
    mensaje.attach(MIMEText(html, "html", "utf-8"))
    return mensaje


class EmailNotificador(NotificadorRecompensa):
    def __init__(self, log_path: Path | None = None) -> None:
        self._log_path = log_path or DEFAULT_LOG
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._from_addr = os.getenv("EMAIL_FROM", "notificaciones@fidelizacion.lab")
        self._smtp_host = os.getenv("EMAIL_SMTP_HOST", "").strip()
        self._smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self._smtp_user = os.getenv("EMAIL_SMTP_USER", "").strip()
        self._smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", "").strip()
        self._smtp_tls = os.getenv("EMAIL_SMTP_TLS", "true").lower() in ("1", "true", "yes")

    def notificar(
        self,
        numero_tarjeta: str,
        puntos_abonados: int,
        saldo_total: int,
        procesado_en: datetime,
        email_cliente: str | None = None,
    ) -> None:
        destinos = _destinatarios(numero_tarjeta, email_cliente)
        destino_log = destinos[0] if destinos else _correo_cliente(numero_tarjeta)
        texto = _cuerpo_texto(numero_tarjeta, puntos_abonados, saldo_total, procesado_en)
        html = _cuerpo_html(numero_tarjeta, puntos_abonados, saldo_total, procesado_en)
        asunto = f"Recompensa procesada (+{puntos_abonados} puntos)"

        registro = (
            f"\n{'=' * 60}\n"
            f"Para: {', '.join(destinos)}\n"
            f"De: {self._from_addr}\n"
            f"Asunto: {asunto}\n"
            f"Formato SMTP: texto + HTML\n"
            f"{'-' * 60}\n"
            f"{texto}\n"
        )
        with self._log_path.open("a", encoding="utf-8") as archivo:
            archivo.write(registro)

        print(f"[EMAIL] Enviado (registrado) a {destino_log} — ver {self._log_path}")

        if self._smtp_host:
            self._enviar_smtp(destinos, asunto, texto, html)

    def _enviar_smtp(
        self,
        destinos: list[str],
        asunto: str,
        texto: str,
        html: str,
    ) -> None:
        mensaje = _crear_mensaje_smtp(destinos, asunto, texto, html, self._from_addr)

        with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=30) as servidor:
            if self._smtp_tls:
                servidor.starttls()
            if self._smtp_user:
                servidor.login(self._smtp_user, self._smtp_password)
            servidor.sendmail(self._from_addr, destinos, mensaje.as_string())
        print(
            f"[EMAIL] SMTP (HTML) enviado a {', '.join(destinos)} via {self._smtp_host}"
        )
