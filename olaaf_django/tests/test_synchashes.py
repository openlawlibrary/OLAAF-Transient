import pytest

from olaaf_django.models import Publication
from olaaf_django.sync_hashes import sync_hashes


def _to_pub_name(p):
  return f"publication/{p.name}"


def test_synchashes(repository, publications, db):
  sync_hashes(repository.path)

  pub_branches = list(publications.keys())
  pub_branches_db = Publication.objects.all()
  assert set(pub_branches) == set([_to_pub_name(p) for p in pub_branches_db])

  for pub in pub_branches_db:
    commits = list(publications[_to_pub_name(pub)].keys())
    commits_db = pub.commit_set.all()

    assert len(commits) == len(commits_db)
