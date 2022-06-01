from collections import defaultdict
from functools import reduce
from operator import concat

import pytest
from lxml import html

from olaaf_django.models import Hash, Publication
from olaaf_django.sync_hashes import sync_hashes
from olaaf_django.tests.conftest import HTML_REPOSITORY_PATH


def _to_pub_branch_name(pub):
  return f"publication/{pub.name}"


def _to_commit_name(pub, commit):
  pub_name = pub.name[0:10]
  return f"{pub_name}/{commit.date}"


def _check_path_url(path):
  tree = html.fromstring((HTML_REPOSITORY_PATH / path.filesystem).read_bytes())
  expected_url_el = tree.xpath(".//meta[contains(@property, 'expected:url')]")
  try:
    expected_url = expected_url_el[0].attrib.get("content")
    assert expected_url == path.url
  except IndexError:
    pytest.fail("Add '<meta property=\"expected:url\" content=\"...\" />' to test html file!")


def test_synchashes(html_repository_and_input, non_publications, publications, repo_files, db):
  html_repository, html_repo_input = html_repository_and_input
  sync_hashes(html_repository.library_dir, html_repo_input)

  pub_branches = list(publications.keys())

  pub_branches_db = Publication.objects.all()
  assert set(pub_branches) == set([_to_pub_branch_name(p) for p in pub_branches_db])

  # check publications
  assert not Publication.objects.get(name="2020-01-01").revoked
  assert Publication.objects.get(name="2020-05-05").revoked
  assert not Publication.objects.get(name="2020-05-05-01").revoked
  # checks if there are just publication branches
  assert Publication.objects.all().count() == len(pub_branches)

  for pub in pub_branches_db:
    html_repository.checkout_branch(f"publication/{pub.name}")

    commits = list(publications[_to_pub_branch_name(pub)].keys())[1:]
    commits_db = pub.commit_set.all()

    assert len(commits) == len(commits_db)
    assert set(commits) == set([_to_commit_name(pub, c) for c in commits_db])

    paths = pub.path_set.all()
    assert set(repo_files) == set([p.filesystem for p in paths])

    for db_path in paths:
      _check_path_url(db_path)

    changed_files = reduce(
        concat,
        # skip first commit because we have one BITSTREAM and one RENDERED hash by default
        [publications[_to_pub_branch_name(pub)][c] for c in commits[1:]], []
    )
    changed_files_hashes_expected_len = defaultdict(lambda: {Hash.BITSTREAM: 1, Hash.RENDERED: 1})
    for f_name, is_auth_changed in changed_files:
      changed_files_hashes_expected_len[f_name][Hash.BITSTREAM] += 1
      if is_auth_changed:
        changed_files_hashes_expected_len[f_name][Hash.RENDERED] += 1

    for f_name, expected_hashes_len in changed_files_hashes_expected_len.items():
      for hash_type, hash_len in changed_files_hashes_expected_len[f_name].items():
        file_hashes_len = Hash.objects.filter(
            path__filesystem=f_name,
            path__publication=pub,
            hash_type=hash_type,
        ).count()

        assert file_hashes_len == hash_len
