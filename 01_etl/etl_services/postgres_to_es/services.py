from functools import wraps
from time import sleep


class ElasticInsertError(Exception):
    ...


def backoff(
          *exceptions,
          logger,
          start_sleep_time=0.1,
          factor=2,
          border_sleep_time=30,
):
    """Функция для повторного выполнения функции через некоторое время."""
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            sleep_time = start_sleep_time
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning("Error. I'll try again in %s seconds.",
                                   sleep_time, exc_info=e)
                    sleep(sleep_time)
                    if sleep_time < border_sleep_time:
                        sleep_time *= factor
                    if sleep_time > border_sleep_time:
                        sleep_time = border_sleep_time
        return inner
    return func_wrapper
