import os
from celery import Celery
# from celery import get_task_logger


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Stock.settings')

# logger = get_task_logger(__name__)

app = Celery('Stock')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
