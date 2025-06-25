from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'

    def ready(self):
        """
        Import signals when the app is ready
        """
        try:
            import quickfund_api.payments.signals
        except ImportError:
            pass