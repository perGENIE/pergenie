from django.test import TestCase
from django.test.utils import override_settings

from .tasks import ping


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class TestCeleryTestCase(TestCase):
    def test_celery_task_ping_ok(self):
        result = ping.delay()
        assert result.successful() == True
        assert result.result == 'pong'
