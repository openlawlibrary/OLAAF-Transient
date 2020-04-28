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
OUTSIDE_TUF_AUTH_DIV_XPATH = "//div[@class='outside-tuf-authenticate']"


# branches as keys | commits and changed files as values
PUBLICATION_BRANCHES = {
    "publication/2020-01-01": {
        "commit1": ["file1.html", "file3.html"],
        "commit2": ["file2.html"],
        "commit3": ["index.html"],
        "commit4": ["file1.html"]
    },
    # "publication/2020-01-01-01": {},
    # "publication/2020-05-05": {},
}


def _checkout_orphan_branch(repo, branch_name):
  """Creates orphan branch"""
  repo._git(f'checkout --orphan {branch_name}')
  try:
    repo._git('rm -rf .')
  except subprocess.CalledProcessError:  # If repository is empty
    pass


def _copy_to_repo(src, dest_dir=REPOSITORY_PATH):
  (dest_dir / src.name).write_text(src.read_text())


def _change_file_content(f, change_tuf_auth_div=True):
  import random
  import string

  random_str = f" {''.join(random.sample(string.ascii_letters, 10))}"

  tree = html.fromstring(f.read_text())
  if change_tuf_auth_div:
    el = tree.xpath(TUF_AUTH_DIV_XPATH)
  else:
    el = tree.xpath(OUTSIDE_TUF_AUTH_DIV_XPATH)

  if len(el):
    el[0].text += random_str

  f.write_text(html.tostring(tree, encoding="utf-8", pretty_print=True).decode("utf-8"))


def _init_pub_branches(repo, branches=PUBLICATION_BRANCHES):
  for branch, commits in branches.items():
    _checkout_orphan_branch(repo, branch)
    # copy initial files
    for f in ALL_FILES:
      _copy_to_repo(f)
    repo.commit("Initial commit.")

    # commit
    for msg, files in commits.items():
      for f in files:
        _change_file_content(REPOSITORY_PATH / f)
      repo.commit(msg)


@pytest.fixture
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
