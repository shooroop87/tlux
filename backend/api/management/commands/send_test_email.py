# api/management/commands/send_test_email.py
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime


class Command(BaseCommand):
    help = (
        "Отправляет тестовое письмо напрямую через SMTP (в обход django-post-office). "
        "Пытается использовать шаблон email/email.html; если его нет — шлёт простой текст."
    )

    def add_arguments(self, parser):
        parser.add_argument("to", nargs="+", help="Кому отправить (один или несколько адресов)")
        parser.add_argument("--subject", default="TLUX test email", help="Тема письма")
        parser.add_argument(
            "--from",
            dest="from_email",
            default=None,
            help="FROM-адрес; по умолчанию settings.DEFAULT_FROM_EMAIL",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Не отправлять, только сгенерировать контент и вывести в консоль",
        )

    def handle(self, *args, **opts):
        to_list = opts["to"]
        subject = opts["subject"]
        from_email = opts["from_email"] or getattr(settings, "DEFAULT_FROM_EMAIL", None)

        if not from_email:
            self.stderr.write(
                self.style.ERROR(
                    "DEFAULT_FROM_EMAIL не задан и --from не указан. "
                    "Установите DEFAULT_FROM_EMAIL в settings или передайте --from."
                )
            )
            return

        # Пример контекста – подставьте поля, которые ожидает ваш шаблон
        context = {
            "booking_id": 123456,
            "customer_name": "Test Customer",
            "customer_email": to_list[0],
            "pickup_address": "Via Roma 1, Milano",
            "dropoff_address": "Aeroporto Malpensa T1",
            "pickup_datetime": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "passengers": 2,
            "luggage": 2,
            "price": "€99.00",
            "payment_method": "Test",
            "notes": "This is a test email sent from management command.",
        }

        # 1) Пытаемся отрендерить HTML-шаблон
        html_body = None
        try:
            html_body = render_to_string("email/email.html", context)
        except TemplateDoesNotExist:
            pass

        if html_body:
            text_body = strip_tags(html_body) or "HTML-only email"
        else:
            # Запасной простой текст, если шаблон не найден
            text_body = (
                "TLUX Test Email\n\n"
                f"Booking: {context['booking_id']}\n"
                f"Customer: {context['customer_name']} ({context['customer_email']})\n"
                f"From: {context['pickup_address']}\n"
                f"To: {context['dropoff_address']}\n"
                f"When: {context['pickup_datetime']}\n"
                f"Passengers: {context['passengers']}, Luggage: {context['luggage']}\n"
                f"Price: {context['price']}\n"
                f"Payment: {context['payment_method']}\n"
                f"Notes: {context['notes']}\n"
            )

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN — письмо не отправлено. Текст ниже:\n"))
            if html_body:
                self.stdout.write(self.style.MIGRATE_HEADING("=== HTML BODY ==="))
                self.stdout.write(html_body)
            self.stdout.write(self.style.MIGRATE_HEADING("\n=== TEXT BODY ==="))
            self.stdout.write(text_body)
            return

        # 2) ВАЖНО: принудительно открываем SMTP-подключение — это обходит post_office
        conn = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            fail_silently=False,  # пусть бросает исключения, чтобы видеть реальные ошибки
        )

        # 3) Сборка письма
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=to_list,
            connection=conn,  # критично для обхода post_office
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        self.stdout.write(
            f"Пытаюсь отправить через {getattr(settings, 'EMAIL_HOST', 'smtp')}:{getattr(settings, 'EMAIL_PORT', '')} "
            f"(SSL={getattr(settings, 'EMAIL_USE_SSL', False)}, TLS={getattr(settings, 'EMAIL_USE_TLS', False)}) "
            f"от {from_email} → {', '.join(to_list)}"
        )

        sent = msg.send(fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f"Готово: отправлено {sent} письм(а)"))
