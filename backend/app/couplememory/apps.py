from django.apps import AppConfig


class CouplememoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'couplememory'

    def ready(self):
            # import signals.py so the handlers register
            import couplememory.signals   # noqa
  