import itertools
from functools import partial

import pytest
from django.test import Client
from django.urls import reverse
from git import Repo
from lxml import html

from olaaf_django import HOSTS_REPOS_CACHE
from olaaf_django.authentication import check_authenticity
from olaaf_django.models import Commit, Publication
from olaaf_django.sync_hashes import sync_hashes


def _get_file_content(repo, url):
  parts = url.split('/', 4)

  pub = parts[1]
  date = parts[3]
  path = parts[4]

  commit = Commit.objects.get(publication__name=pub, date=date)

  # TODO: encode url component?
  content = repo.git.show('{}:{}'.format(commit.sha, path))

  # replace links inside html doc
  tree = html.fromstring(content)
  try:
    link = tree.get_element_by_id("test-url")
    link.attrib['href'] = f"/{'/'.join(parts[:4])}{link.attrib['href']}"
  except KeyError:
    pass

  return html.tostring(tree, encoding="utf-8").decode("utf-8")


def test_html_authentication(repository, publications, repo_files, db):
  repo = Repo(repository.path)

  sync_hashes(repository.path)
  # update revoked publication
  Publication.objects.filter(name="2020-01-01").update(revoked=False)

  # list of urls like '_publication/2020-01-01/_date/2019-01-01/index.html'
  test_urls = list([
      f"{x[0]}/{x[1]}" for x in itertools.product(
          [f"_{pub_name}/_date/{commit[11:]}" for pub_name, commits in publications.items()
           for commit in list(commits.keys())[1:]],
          repo_files
      )])

  # Add test host
  HOSTS_REPOS_CACHE['testserver'] = 'tests/repository'

  client = Client()
  auth_post = partial(client.post, reverse('authenticate'))
  for url in test_urls:
    response = auth_post(data={'url': url, 'content': _get_file_content(repo, url)})

    if url.startswith('_publication/2020-05-05'):  # this one is revoked and will return 404
      assert response.status_code == 404
    else:
      assert response.status_code == 200
