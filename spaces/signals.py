from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, ConfirmEmailToken
from django_rest_passwordreset.signals import reset_password_token_created


@receiver(post_save, sender=User)
def create_confirm_email_token(sender, instance, created, **kwargs):
    """
    Сигнал: при создании нового пользователя создаем токен и отправляем email
    """
    if created:
        # Создаем токен (ключ сгенерируется сам благодаря твоему методу save() в модели)
        token = ConfirmEmailToken.objects.create(user=instance)

        # Отправляем письмо
        send_mail(
            subject='Подтверждение регистрации в Коворкинге',
            message=f'Здравствуйте, {instance.name_user}!\n\nВаш токен для подтверждения: {token.key}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Сигнал: при создании токена сброса пароля отправляем email
    """
    send_mail(
        subject='Сброс пароля в Коворкинге',
        message=f'Здравствуйте, {reset_password_token.user.name_user}!\n\nВаш токен для сброса пароля: {reset_password_token.key}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reset_password_token.user.email],
        fail_silently=False,
    )