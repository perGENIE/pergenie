from celery.decorators import task


@task
def ping():
    return 'pong'
