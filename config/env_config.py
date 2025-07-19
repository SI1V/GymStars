from pydantic.types import SecretStr
from config.base_conf import ConfigBase


class TelegramConfig(ConfigBase):
    bot_token: SecretStr


class DatabaseConfig(ConfigBase):
    database_url: str
    sql_echo: bool


class LogConfig(ConfigBase):
    log_format: str
    log_level: str
    log_file_path: str
    log_rotation: str
    log_retention: str
    log_compression: str
    log_to_console: bool


