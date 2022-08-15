import logging
import mimetypes
from pathlib import Path

from django.http import Http404

logger = logging.getLogger('django')


HOSTS_REPOS_CACHE = {}


def set_hosts_repos_cache_from_settings(settings):
  try:
    global HOSTS_REPOS_CACHE
    HOSTS_REPOS_CACHE = settings.HOSTS_REPOS_CACHE
  except AttributeError:
    logger.error("Could not read 'HOSTS_REPOS_CACHE' from settings")


def get_repo_by_host(host):
  """Return partner repo for a given host and repo_type."""
  try:
    return HOSTS_REPOS_CACHE[host]
  except KeyError:
    logger.debug('%s host is not in HOSTS_REPOS_CACHE!', host)
    raise


def get_repo_info(host, path=None):
  """Get repository information from host."""
  try:
    content_type = mimetypes.guess_type(path or '')[0] or 'text/html'
    repo_name = get_repo_by_host(host)
    return repo_name, content_type
  except KeyError:
    raise Http404()
