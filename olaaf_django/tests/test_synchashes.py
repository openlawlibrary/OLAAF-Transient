from functools import reduce
from operator import concat

import pytest
from lxml import html

from olaaf_django.models import Hash, Publication
from olaaf_django.sync_hashes import sync_hashes


def _to_pub_name(pub):
  return f"publication/{pub.name}"


def _to_commit_name(pub, commit):
  pub_name = pub.name[0:10]
  return f"{pub_name}/{commit.date}"


def test_synchashes(repository, publications, repo_files, db):
  sync_hashes(repository.path)

  pub_branches = list(publications.keys())
  pub_branches_db = Publication.objects.all()
  assert set(pub_branches) == set([_to_pub_name(p) for p in pub_branches_db])

  for pub in pub_branches_db:
    commits = list(publications[_to_pub_name(pub)].keys())
    commits_db = pub.commit_set.all()

    assert len(commits) == len(commits_db)
    assert set(commits) == set([_to_commit_name(pub, c) for c in commits_db])

    paths = pub.path_set.all()
    assert set(repo_files) == set([p.filesystem for p in paths])
    # TODO: Check url

    hashes = reduce(concat, [list(p.hash_set.all()) for p in paths], [])
