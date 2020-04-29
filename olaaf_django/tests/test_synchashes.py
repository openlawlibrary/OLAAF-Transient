from functools import reduce
from operator import concat

import pytest
from lxml import html

from olaaf_django.models import Hash, Publication
from olaaf_django.sync_hashes import sync_hashes
from olaaf_django.tests.conftest import REPOSITORY_PATH


def _to_pub_name(pub):
  return f"publication/{pub.name}"


def _to_commit_name(pub, commit):
  pub_name = pub.name[0:10]
  return f"{pub_name}/{commit.date}"


def _check_path_url(path):
  tree = html.fromstring((REPOSITORY_PATH / path.filesystem).read_bytes())
  expected_url_el = tree.xpath(".//meta[contains(@property, 'test:url')]")
  try:
    expected_url = expected_url_el[0].attrib.get("content")
    assert expected_url == path.url
  except IndexError:
    pytest.fail("Add '<meta property=\"test:url\" content=\"...\" />' to test html file!")


def test_synchashes(repository, publications, repo_files, db):
  sync_hashes(repository.path)

  pub_branches = list(publications.keys())
  # this one is skipped in favor of publication/2020-05-05-01
  pub_branches.remove("publication/2020-05-05")

  pub_branches_db = Publication.objects.all()
  assert set(pub_branches) == set([_to_pub_name(p) for p in pub_branches_db])

  # same date publication should be revoked
  assert Publication.objects.get(name="2020-01-01").revoked

  for pub in pub_branches_db:
    commits = list(publications[_to_pub_name(pub)].keys())[1:]
    commits_db = pub.commit_set.all()

    assert len(commits) == len(commits_db)
    assert set(commits) == set([_to_commit_name(pub, c) for c in commits_db])

    paths = pub.path_set.all()
    assert set(repo_files) == set([p.filesystem for p in paths])

    for db_path in paths:
      _check_path_url(db_path)

    changed_files = reduce(concat, [publications[_to_pub_name(pub)][c] for c in commits], [])
    changed_files_hashes_expected_len = {}
    for f_name, is_auth_changed in changed_files:
      changed_files_hashes_expected_len[f_name] = \
          changed_files_hashes_expected_len.get(f_name, 1) + int(is_auth_changed) + 1

    for f_name, expected_hashes_len in changed_files_hashes_expected_len.items():
      file_hashes = Hash.objects.filter(path__filesystem=f_name, path__publication=pub)

      assert len(file_hashes) == expected_hashes_len
