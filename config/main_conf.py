from config.base_conf import ConfigBase
from config.env_config import TelegramConfig, DatabaseConfig, LogConfig
from pydantic import Field

class Settings(ConfigBase):
    tg: TelegramConfig = Field(default_factory=TelegramConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    log: LogConfig = Field(default_factory=LogConfig)

settings = Settings()
