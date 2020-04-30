import shutil
import subprocess
from pathlib import Path

import pytest
from lxml import html
from taf.git import GitRepository

THIS_FOLDER = Path(__file__).parent

DATA = THIS_FOLDER / "data"
ALL_FILES = list(DATA.rglob("*"))

REPOSITORY_PATH = THIS_FOLDER / "repository"

TUF_AUTH_DIV_XPATH = "//div[@class='tuf-authenticate']"
OUTSIDE_TUF_AUTH_DIV_XPATH = "//div[@class='no-authenticate']"


# branches as keys | commits and changed files as values
PUBLICATION_BRANCHES = {
    "publication/2020-01-01": {
        "publication/2020-01-01": [],  # empty commit
        "2020-01-01/2019-01-01": [(f.name, False) for f in ALL_FILES],  # 4 files * (B|R) = 8 hashes
        "2020-01-01/2019-02-02": [  # 2 files * (B|R) = 4 hashes
            # file name, auth div change
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


@pytest.fixture(scope='session')
def repository():
  try:
    repo = GitRepository(str(REPOSITORY_PATH))
    repo.init_repo()
    _init_pub_branches(repo)
    yield repo
  except KeyboardInterrupt:
    pass
  except Exception:
    raise
  finally:
    shutil.rmtree(REPOSITORY_PATH)
    REPOSITORY_PATH.mkdir()
    (REPOSITORY_PATH / ".gitkeep").touch()


@pytest.fixture
def publications():
  return PUBLICATION_BRANCHES


@pytest.fixture
def repo_files():
  return [str(f.relative_to(DATA)) for f in ALL_FILES]


def _init_pub_branches(repo, branches=PUBLICATION_BRANCHES):
  for branch, commits in branches.items():
    _checkout_orphan_branch(repo, branch)
    # commit
    for msg, file_changes in commits.items():
      if len(file_changes):
        for f_name, is_auth_change in file_changes:
          src_path = DATA / f_name
          dest_path = REPOSITORY_PATH / f_name
          if not dest_path.exists():
            _copy_to_repo(src_path)
          dest_path.write_text(_change_file_content(dest_path.read_text(), is_auth_change))

        repo.commit(msg)
      else:
        repo.commit_empty(msg)


def _checkout_orphan_branch(repo, branch_name):
  """Creates orphan branch"""
  repo._git(f'checkout --orphan {branch_name}')
  try:
    repo._git('rm -rf .')
  except subprocess.CalledProcessError:  # If repository is empty
    pass


def _copy_to_repo(src, dest_dir=REPOSITORY_PATH):
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
