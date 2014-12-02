from .base import EnvSettings
from .cache import CacheConfig
from .database import DatabaseConfig
from .email import EmailConfig


envsettings = EnvSettings()

get = envsettings.get
get_int = envsettings.get_int
get_bool = envsettings.get_bool

cache = CacheConfig()
database = DatabaseConfig()
email = EmailConfig()
