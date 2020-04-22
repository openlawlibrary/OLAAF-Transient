from django.apps import AppConfig

from django.conf import settings
from . import set_hosts_repos_cache_from_settings


class OLAAFDjangoConfig(AppConfig):
  name = 'olaaf_django'

  def ready(self):
    set_hosts_repos_cache_from_settings(settings)
