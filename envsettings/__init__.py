from .base import EnvSettings
from .cache import CacheSettings
from .database import DatabaseSettings
from .email import EmailSettings
from .logging import LoggingSettings


envsettings = EnvSettings()

get = envsettings.get
get_int = envsettings.get_int
get_bool = envsettings.get_bool

cache = CacheSettings()
database = DatabaseSettings()
email = EmailSettings()
logging = LoggingSettings()
