import itertools
import random
from functools import partial

import pytest
from django.db.models import Q, Subquery
from django.test import Client
from django.urls import reverse
from git import Repo
from lxml import html

from olaaf_django import HOSTS_REPOS_CACHE
from olaaf_django.authentication import check_authenticity
from olaaf_django.models import Commit, Publication
from olaaf_django.sync_hashes import _get_document, sync_hashes
from olaaf_django.tests.conftest import _change_file_content


def _get_file_content(chrome_driver, repo, url, change_auth_div=False):
  parts = url.split('/', 4)

  pub = parts[1]
  date = parts[3]
  path = parts[4]

  commit = Commit.objects.get(
      publication__name=Subquery(
          Publication.objects
          .filter(name__startswith=pub)
          .order_by('-name')
          .values_list('name')[:1]
      ),
      date=date,
  )

  content = repo.git.show('{}:{}'.format(commit.sha, path))

  if change_auth_div:
    content = _change_file_content(content)
  # replace links inside html doc
  document = _get_document(content.strip().encode('utf-8', 'surrogateescape'), chrome_driver)
  try:
    link = document.get_element_by_id("test-url")
    link.attrib['href'] = f"/{'/'.join(parts[:4])}{link.attrib['href']}"
  except KeyError:
    pass

  return html.tostring(document, encoding="utf-8").decode("utf-8")


def test_html_authentication(html_repository_and_input, publications, repo_files, chrome_driver, db):
  html_repository, html_repo_input = html_repository_and_input
  repo = Repo(html_repository.path)

  sync_hashes(html_repository.root_dir, html_repo_input)

  # list of urls like '_publication/2020-01-01/_date/2019-01-01/index.html'
  test_urls = list([
      f"{x[0]}/{x[1]}" for x in itertools.product(
          [f"_{pub_name}/_date/{commit[11:]}" for pub_name, commits in publications.items()
           for commit in list(commits.keys())[1:]],
          repo_files
      )])

  # Add test host
  HOSTS_REPOS_CACHE['testserver'] = 'test/html-repo'

  client = Client()
  auth_post = partial(client.post, reverse('authenticate'))

  for url in test_urls:
    change_auth_div = bool(random.getrandbits(1))

    response = auth_post(
        data={
            'url': url,
            'content': _get_file_content(chrome_driver, repo, url, change_auth_div=change_auth_div)
        }
    )

    if url.startswith('_publication/2020-05-05/'):  # this one is revoked and will always return 404
      assert response.status_code == 404
    else:
      assert response.status_code == 200
      msg = ' '.join([l.decode() for l in response.content.strip().splitlines()])

      if change_auth_div:
        assert msg.startswith('Not authentic')
      else:
        assert msg.startswith('Authentic')
