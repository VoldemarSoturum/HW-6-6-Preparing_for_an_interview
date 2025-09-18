
#===================Код после выполнения рефакторинга и разбора хардкорных участков кода=============
from __future__ import annotations  # отложенная (ленивая) оценка аннотаций типов; полезно при перекрёстных ссылках и для совместимости

import email                        # стандартный модуль для работы с письмами (парсинг MIME и т.п.)
import imaplib                      # IMAP-клиент из стандартной библиотеки (получение писем)
import smtplib                      # SMTP-клиент из стандартной библиотеки (отправка писем)
from dataclasses import dataclass   # декоратор для краткого объявления "контейнеров данных"
from email.message import EmailMessage  # современный удобный класс для сборки письма (вместо старых MIME* модулей)
from typing import Iterable, Optional, Sequence, Tuple  # типы для подсказок и читаемости


@dataclass
class MailClient:
    """Клиент почты с методами отправки (SMTP) и получения (IMAP)."""
    # dataclass автоматически сгенерирует __init__, __repr__, __eq__ и т.д., используя поля ниже

    username: str                               # адрес отправителя/логин для SMTP/IMAP
    password: str                               # пароль (для Gmail обычно App Password при включённой 2FA)
    smtp_server: str = "smtp.gmail.com"         # хост SMTP по умолчанию
    smtp_port: int = 587                        # порт SMTP (587 — STARTTLS)
    imap_server: str = "imap.gmail.com"         # хост IMAP по умолчанию
    imap_port: int = 993                        # порт IMAP (993 — IMAPS/SSL)
    smtp_use_tls: bool = True                   # использовать ли STARTTLS при отправке
    timeout: int = 60                           # таймаут сетевых операций в секундах

    # ---------- SMTP ----------
    def send_email(
        self,
        recipients: Sequence[str],              # список получателей (To)
        subject: str,                           # тема письма
        body: str,                              # текст письма (plain text)
        *,
        cc: Sequence[str] | None = None,        # получатели в копии (Cc)
        bcc: Sequence[str] | None = None,       # получатели в скрытой копии (Bcc) — не попадают в заголовок письма
        attachments: Iterable[Tuple[str, bytes, str]] | None = None,  # вложения: (имя файла, содержимое байтами, MIME-тип)
    ) -> None:
        """Отправить письмо.

        attachments: итерируемый набор кортежей (filename, content_bytes, mime_type)
                     например: [("readme.txt", b"...", "text/plain")]
        """
        cc = cc or []                           # нормализуем None -> [] для единообразной обработки
        bcc = bcc or []
        attachments = attachments or []

        msg = EmailMessage()                    # создаём объект письма
        msg["From"] = self.username             # заголовок From
        msg["To"] = ", ".join(recipients)       # заголовок To — строка с адресами через запятую
        if cc:
            msg["Cc"] = ", ".join(cc)           # заголовок Cc добавляем только если список непустой
        msg["Subject"] = subject                # тема письма
        msg.set_content(body)                   # тело письма как text/plain

        for filename, content, mime_type in attachments:   # перебираем вложения
            maintype, subtype = mime_type.split("/", 1)    # делим MIME-тип на основную и подтип (например, "text/plain")
            msg.add_attachment(
                content,                                   # байтовое содержимое файла
                maintype=maintype,                         # основная часть MIME-типа
                subtype=subtype,                           # подтип MIME
                filename=filename,                         # имя файла, которое увидит получатель
            )

        all_rcpts = list(recipients) + list(cc) + list(bcc)  # фактические адресаты SMTP (Bcc здесь обязателен, в заголовок не добавляется)

        # Создаём SMTP-соединение с таймаутом; контекстный менеджер гарантирует закрытие соединения
        with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as s:
            s.ehlo()                                       # приветствуем сервер и объявляем себя (идентификация клиента)
            if self.smtp_use_tls:
                s.starttls()                               # переключаемся на защищённый канал (STARTTLS)
                s.ehlo()                                   # повторная идентификация после установки TLS
            s.login(self.username, self.password)          # аутентификация на SMTP-сервере
            # send_message сам подставит From/To из msg, но мы явным образом передаём список адресатов (включая Bcc)
            s.send_message(msg, from_addr=self.username, to_addrs=all_rcpts)

    # ---------- IMAP ----------
    def fetch_latest(
        self,
        mailbox: str = "INBOX",                            # папка почты (в Gmail регистрозависимая: "INBOX")
        *,
        subject: Optional[str] = None,                     # необязательный фильтр по теме (точнее — по заголовку Subject)
        unread_only: bool = False,                         # если True — искать только непрочитанные
    ) -> Optional[email.message.Message]:
        """Получить последнее письмо по критериям (или None, если не найдено)."""
        # Используем IMAP по SSL (IMAPS). Контекстный менеджер закроет соединение.
        with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as imap:
            imap.login(self.username, self.password)       # логин на IMAP-сервере
            imap.select(mailbox)                           # выбираем почтовый ящик/папку

            criteria = ["ALL"]                             # базовый критерий поиска: все письма
            if unread_only:
                criteria.append("UNSEEN")                  # добавляем фильтр непрочитанных
            if subject:
                safe_subject = subject.replace('"', r"\"") # экранируем кавычки, чтобы не сломать IMAP-критерий
                criteria.append(f'(HEADER Subject "{safe_subject}")')  # фильтр по заголовку Subject

            search_query = " ".join(criteria)              # собираем финальную строку критериев
            status, data = imap.uid("search", None, search_query)  # ищем по UIDs; data[0] — байтовая строка с uid через пробел
            if status != "OK" or not data or not data[0]:  # если ошибка или ничего не найдено
                return None

            latest_uid = data[0].split()[-1]               # берём последний UID из результата (последнее по времени письмо)
            status, fetched = imap.uid("fetch", latest_uid, "(RFC822)")  # запрашиваем целиком сырой RFC822 контент
            if status != "OK" or not fetched or not fetched[0]:
                return None

            raw_email = fetched[0][1]                      # bytes с содержимым письма
            return email.message_from_bytes(raw_email)     # парсим в объект email.message.Message

    # ---------- Helpers ----------
    @staticmethod
    def extract_text(msg: email.message.Message) -> str:
        """Достать текстовую часть письма (text/plain) без вложений."""
        parts: list[str] = []                              # копим фрагменты текста (если multipart может быть несколько)
        if msg.is_multipart():                             # если письмо многочастное (multipart/*)
            for part in msg.walk():                        # обходим все части (вложенные секции MIME)
                ctype = part.get_content_type()            # MIME-тип части
                disp = part.get("Content-Disposition", "") # Content-Disposition (attachment/inline/пусто)
                if ctype == "text/plain" and "attachment" not in disp:  # отбираем только текст без вложений
                    charset = part.get_content_charset() or "utf-8"     # кодировка, по умолчанию utf-8
                    payload = part.get_payload(decode=True)             # берём байты содержимого
                    if payload is not None:
                        parts.append(payload.decode(charset, errors="replace"))  # декодируем с заменой битых символов
        else:                                              # односоставное письмо (без multipart)
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload is not None:
                parts.append(payload.decode(charset, errors="replace"))
        return "\n".join(parts).strip()                    # объединяем все найденные текстовые части в одну строку


if __name__ == "__main__":                                 # исполняем только при запуске файла как скрипта (не при импорте как модуля)
    # Пример CLI-использования без хардкода.
    # Пароли лучше передавать как APP PASSWORD (для Gmail) и не хранить в коде.
    import argparse                                        # парсер аргументов командной строки
    import getpass                                         # безопасный ввод пароля без эха
    import os                                              # доступ к переменным окружения

    parser = argparse.ArgumentParser(description="SMTP/IMAP почтовый клиент")  # создаём парсер CLI
    parser.add_argument(
        "-u",
        "--username",
        default=os.environ.get("MAIL_USER"),               # можно передать логин через переменную окружения MAIL_USER
        help="логин (email), можно через переменную окружения MAIL_USER",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=os.environ.get("MAIL_PASS"),               # пароль можно передать через MAIL_PASS (или ввести интерактивно)
        help="пароль (лучше APP PASSWORD); можно через MAIL_PASS; "
             "если не указать — спрошу интерактивно",
    )
    parser.add_argument("--smtp", default=os.environ.get("SMTP_SERVER", "smtp.gmail.com"))  # SMTP-хост (по умолчанию gmail)
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("SMTP_PORT", 587)))  # SMTP-порт
    parser.add_argument("--imap", default=os.environ.get("IMAP_SERVER", "imap.gmail.com"))  # IMAP-хост
    parser.add_argument("--imap-port", type=int, default=int(os.environ.get("IMAP_PORT", 993)))  # IMAP-порт
    parser.add_argument("--no-tls", action="store_true", help="не использовать STARTTLS для SMTP")  # флаг для отключения TLS

    sub = parser.add_subparsers(dest="cmd", required=True)  # подкоманды: send/recv (обязательны)

    p_send = sub.add_parser("send", help="отправить письмо")  # описываем подкоманду send
    p_send.add_argument("--to", nargs="+", required=True, help="получатели")            # один или несколько адресатов
    p_send.add_argument("--cc", nargs="*", default=[], help="копия")                    # список адресов Cc
    p_send.add_argument("--bcc", nargs="*", default=[], help="скрытая копия")           # список адресов Bcc
    p_send.add_argument("--subject", required=True)                                     # тема
    p_send.add_argument("--body", required=True)                                        # тело письма (plain text)

    p_recv = sub.add_parser("recv", help="получить последнее письмо")  # описываем подкоманду recv
    p_recv.add_argument("--mailbox", default="INBOX")                                  # папка (INBOX по умолчанию)
    p_recv.add_argument("--subject", help="фильтр по теме (HEADER Subject ...)")       # фильтр по теме (опционально)
    p_recv.add_argument("--unread", action="store_true", help="только непрочитанные")  # только непрочитанные

    args = parser.parse_args()                                # разбираем аргументы командной строки

    if not args.username:                                     # если логин не пришёл ни из CLI, ни из окружения —
        args.username = input("Email login: ").strip()        # спросим интерактивно

    if not args.password:                                     # если пароль не пришёл ни из CLI, ни из окружения —
        args.password = getpass.getpass("Email password (app password recommended): ")  # запросим безопасно

    client = MailClient(                                      # создаём экземпляр клиента с собранными параметрами
        username=args.username,
        password=args.password,
        smtp_server=args.smtp,
        smtp_port=args.smtp_port,
        imap_server=args.imap,
        imap_port=args.imap_port,
        smtp_use_tls=not args.no_tls,                         # если указан --no-tls, то tls=False
    )

    if args.cmd == "send":                                    # обработка подкоманды отправки
        client.send_email(
            recipients=args.to,
            subject=args.subject,
            body=args.body,
            cc=args.cc,
            bcc=args.bcc,
        )
        print("Письмо отправлено.")                           # уведомление об успешной отправке
    elif args.cmd == "recv":                                  # обработка подкоманды получения
        msg = client.fetch_latest(
            mailbox=args.mailbox,
            subject=args.subject,
            unread_only=args.unread,
        )
        if msg is None:                                       # если ничего не нашли по критериям
            print("Писем по заданным критериям не найдено.")
        else:                                                 # выводим ключевые заголовки и текстовую часть
            print("— From:", msg.get("From", ""))
            print("— Subject:", msg.get("Subject", ""))
            print("— Date:", msg.get("Date", ""))
            print("— Body:\n" + MailClient.extract_text(msg))
