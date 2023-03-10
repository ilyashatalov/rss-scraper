import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Class for environment variable parsing and accurate types conversion.
    There are some usual problems with types when using dotenv lib.
    """

    __defaults = {
        "MAX_RETRIES": 3,
        "SCHEDULE_INTERVAL_SEC": 10,
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "SMTP_SERVER": "",
        "SMTP_PORT": 587,
        "SMTP_LOGIN": "",
        "SMTP_PASSWORD": "",
        "NOTIFICATION": False,
        "NOTIFICATION_TYPE": "email",
    }
    __integer_keys = ("MAX_RETRIES", "SCHEDULE_INTERVAL_SEC", "SMTP_PORT")
    __boolean_keys = ("NOTIFICATION",)

    __config = {}

    def __new__(cls):
        instance = super().__new__(cls)
        instance.get_config()
        return instance

    def __parse(self):
        for key in self.__defaults.keys():
            if key in self.__integer_keys and key in os.environ:
                value = int(os.environ.get(key))
                self.__config[key] = value
            elif key in self.__boolean_keys and key in os.environ:
                value = os.getenv(key, 'False').lower() in ('true', '1', 't')
                self.__config[key] = value
            else:
                self.__config[key] = self.__defaults[key]
        return self.__config

    def get_config(self):
        return self.__parse()
