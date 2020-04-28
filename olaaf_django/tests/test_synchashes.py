from olaaf_django.models import Publication
from olaaf_django.sync_hashes import sync_hashes


def test_synchashes(repository, db):
  sync_hashes(repository.path)
