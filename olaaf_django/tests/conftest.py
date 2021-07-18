import os
import json
import shutil
import stat
from pathlib import Path
from collections import defaultdict

import pytest
from lxml import html
from selenium import webdriver
from taf.git import GitRepository

from olaaf_django.sync_hashes import chrome_options

THIS_FOLDER = Path(__file__).parent

DATA = THIS_FOLDER / "data"
ALL_FILES = list(DATA.rglob("*"))

LIBRARY_ROOT = THIS_FOLDER / "library"
HTML_REPO_NAME = "test/html-repo"
HTML_REPOSITORY_PATH = LIBRARY_ROOT / HTML_REPO_NAME

TUF_AUTH_DIV_XPATH = "//div[@class='tuf-authenticate']"
OUTSIDE_TUF_AUTH_DIV_XPATH = "//div[@class='no-authenticate']"


# branches as keys | commits and changed files as values
PUBLICATION_BRANCHES = {
    "publication/2020-01-01": {
        "publication/2020-01-01": [],  # empty commit
        "2020-01-01/2019-01-01": [(f.name, False) for f in ALL_FILES],  # 4 files * (B|R) = 8 hashes
        "2020-01-01/2019-02-02": [  # 2 files * (B|R) = 4 hashes
            # file name, indicator if content of the authenticated div is modified
            ("file1.html", True),
            ("file3.html", True)
        ],
        "2020-01-01/2019-03-03": [  # 1 file * (B|R) = 2 hashes
            ("file2.html", True)
        ],
        "2020-01-01/2019-04-04": [  # 1 file * (B|R) = 2 hashes
            ("index.html", True)
        ],
        "2020-01-01/2019-05-05": [  # 1 file * (B) = 1 hashes
            ("file1.html", False)
        ]
    },
    "publication/2020-05-05": {
        "publication/2020-05-05": [],
        "2020-05-05/2019-01-01": [(f.name, False) for f in ALL_FILES],
        "2020-05-05/2019-02-02": [
            ("file1.html", True),
            ("file3.html", True)
        ],
        "2020-05-05/2019-03-03": [
            ("file2.html", True)
        ],
        "2020-05-05/2019-04-04": [
            ("index.html", True)
        ],
        "2020-05-05/2019-05-05": [
            ("file1.html", False)
        ],
        "2020-05-05/2019-06-06": [
            ("file2.html", False)
        ],
        "2020-05-05/2019-07-07": [
            ("index.html", True)
        ],
    },
    "publication/2020-05-05-01": {  # publication/2020-05-05  will be skipped
        "publication/2020-05-05-01": [],
        "2020-05-05/2019-01-01": [(f.name, False) for f in ALL_FILES],
        "2020-05-05/2019-02-02": [
            ("file1.html", True),
            ("file3.html", True)
        ],
        "2020-05-05/2019-03-03": [
            ("file2.html", True)
        ],
        "2020-05-05/2019-04-04": [
            ("index.html", True)
        ],
        "2020-05-05/2019-05-05": [
            ("file1.html", False)
        ],
        "2020-05-05/2019-06-06": [
            ("file2.html", False)
        ],
        "2020-05-05/2019-07-07": [
            ("index.html", True)
        ],
        "2020-05-05/2019-08-08": [
            ("index.html", True)
        ],
        "2020-05-05/2019-09-09": [
            ("file2.html", True)
        ],
        "2020-05-05/2019-10-10": [
            ("file3.html", True)
        ],
    },
}

NON_PUBLICATION_BRANCHES = {
    "publication/2020-01": {},
    "publication/2020-01-01-01-01": {},
    "publication/2020-01-01.2020-01-04": {},
    "test": {},
}


@pytest.fixture(scope='session')
def html_repository_and_input():
  try:
    repo = GitRepository(LIBRARY_ROOT, HTML_REPO_NAME)
    repo.init_repo()
    repos_data = _init_pub_branches(repo)
    yield repo, repos_data
  except KeyboardInterrupt:
    pass
  except Exception:
    raise
  finally:
    shutil.rmtree(HTML_REPOSITORY_PATH, onerror=_onerror)
    HTML_REPOSITORY_PATH.mkdir()
    (HTML_REPOSITORY_PATH / ".gitkeep").touch()


@pytest.fixture
def publications():
  return PUBLICATION_BRANCHES


@pytest.fixture
def non_publications():
  return NON_PUBLICATION_BRANCHES


@pytest.fixture
def repo_files():
  return [str(f.relative_to(DATA)) for f in ALL_FILES]


@pytest.fixture(scope='session')
def chrome_driver():
  with webdriver.Chrome(options=chrome_options) as driver:
    yield driver


def _init_pub_branches(repo, branches=PUBLICATION_BRANCHES):
  # create publication branches and synchashes input json
  repos_data = {repo.name: defaultdict(list)}
  for branch, commits in branches.items():
    repo.checkout_orphan_branch(branch)
    # commit
    for msg, file_changes in commits.items():
      if len(file_changes):
        for f_name, is_auth_change in file_changes:
          src_path = DATA / f_name
          dest_path = HTML_REPOSITORY_PATH / f_name
          if not dest_path.exists():
            _copy_to_repo(src_path)
          dest_path.write_text(_change_file_content(dest_path.read_text(), is_auth_change))

        sha = repo.commit(msg)
      else:
        sha = repo.commit_empty(msg)

      build_date, codified_date = msg.split('/')
      if build_date == 'publication':
        continue
      additional_info = {"build-date": build_date}
      if codified_date is not None:
        additional_info["codified-date"] = codified_date

      repos_data[repo.name][branch].append(
        {
          "commit": sha,
          "additional-info": additional_info
        }
      )

  # create non publication branches
  for branch in NON_PUBLICATION_BRANCHES.keys():
    repo.checkout_orphan_branch(branch)
    repo.commit_empty("Non publication branch")

  return json.dumps(repos_data)


def _copy_to_repo(src, dest_dir=HTML_REPOSITORY_PATH):
  (dest_dir / src.name).write_text(src.read_text())


def _change_file_content(content, change_tuf_auth_div=True):
  import random
  import string

  random_str = f" {''.join(random.sample(string.ascii_letters, 10))}"

  tree = html.fromstring(content)
  if change_tuf_auth_div:
    el = tree.xpath(TUF_AUTH_DIV_XPATH)
  else:
    el = tree.xpath(OUTSIDE_TUF_AUTH_DIV_XPATH)

  if len(el):
    el[0].text += random_str

  return html.tostring(tree, encoding="utf-8", pretty_print=True).decode("utf-8")


def _onerror(_func, path, _exc_info):
  """Used by when calling rmtree to ensure that readonly files and folders
  are deleted.
  """
  os.chmod(path, stat.S_IWRITE)
  os.unlink(path)
