from django.apps import AppConfig

class SpacesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spaces'
    verbose_name = 'Управление коворкингом'

    def ready(self):
        # Подключаем сигналы при запуске приложения
        import spaces.signals