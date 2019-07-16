import os
import posixpath
from git import Repo
from datetime import datetime
from selenium import webdriver
from django.core.wsgi import get_wsgi_application
from pathlib import Path
import tempfile
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authsite.settings")
application = get_wsgi_application()

from transient_auth.models import Commit, Hash, Edition, Repository
from transient_auth.utils import calc_file_hash, calc_page_hash

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(chrome_options=options)

EMPTY_TREE_SHA = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

def initialize_hashes(repo_path):
  repo_path = Path(repo_path)
  repo_name = '{}/{}'.format(repo_path.parent.name, repo_path.name)
  repo = Repo(str(repo_path))
  repo_commits = list(repo.iter_commits('master'))[::-1]

  # TODO we need to know when an edition ends and where it begins
  # since editions are on branches, maybe use them
  # or call this edition by edition

  repository = Repository.objects.filter(name=repo_name).first()
  if repository is None:
    repository = Repository(name=repo_name)
    repository.save()
    edition = None
  else:
    # update the latest edition
    edition = Edition.objects.filter(repository=repository).latest('id')

  if edition is None:
    # create the initial edition
    commit_date = repo.git.show(s=True, format='%ci {}'.format(repo_commits[0].hexsha)).split()[0]
    edition_name = commit_date.rsplit('-', 1)[0]
    edition = Edition(name=edition_name, date=commit_date, repository=repository)
    edition.save()

  # check if commits are already in the database
  # if they are, see if there are commits which have not been inserted yet
  # if not, insert the hashes from the beginning
  inserted_commits = Commit.objects.filter(edition=edition)[::1]
  if len(inserted_commits) == len(repo_commits):
    print('All commits have been loaded into the database')
    return

  # find the last inserted commit
  inserted_commits_num = len(inserted_commits)
  if inserted_commits_num == 0:
    prev_commit = Commit(sha=EMPTY_TREE_SHA)
  else:
    prev_commit = inserted_commits[-1]

  for commit in repo_commits[inserted_commits_num::]:
    date = datetime.utcfromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M')
    current_commit = Commit(edition=edition, sha=commit.hexsha, date=date)
    current_commit.save()
    _insert_diff_hashes(repo, prev_commit, current_commit)
    prev_commit = current_commit


def _insert_diff_hashes(repo, prev_commit, current_commit):

  print('Inserting diff hashes. Previous commit {} current commit {}'.format(prev_commit,
                                                                             current_commit))
  diff = repo.git.diff('--name-status', prev_commit.sha, current_commit.sha)
  diff_names = diff.split('\n')
  for changed_file in diff_names:
    # we do not want to calculate hashes of index pages, images, json files etc.
    if changed_file.endswith('.html') or changed_file.endswith('.pdf'):
      # git diff contains list of entries in the form of
      # M/A file_name.html
      # so remove the modified/added indicator (first letter) and whitespaces
      action, file_name = changed_file.split(maxsplit=1)
      path = file_name.replace(os.sep, '/')
      # if file was added or modified, calculate the new hash
      if file_name.endswith('.html'):
        url = path.rsplit('.', 1)[0]
      # if file aready existed and it was modified or deleted update previous hash
      if action != 'A':
        previous_hash = Hash.objects.get(path=url, end_commit__isnull=True)
        previous_hash.end_commit = current_commit
        previous_hash.save()
      if action != 'D':
        hash_value = _calculate_file_hash(repo, path, current_commit)
        if hash_value is not None:
          h = Hash(value=hash_value, path=url, start_commit=current_commit)
          h.save()


def _calculate_file_hash(repo, path, commit):
  # save file content to a temporary file
  file_contents = repo.git.show('{}:{}'.format(commit.sha, path))
  temp_dir = tempfile.gettempdir()
  # the file must have .html extension
  # if that is not the case, the browser will not open it correctly
  file_path = os.path.join(temp_dir, str(uuid.uuid4()) + '.html')
  try:
    with open(file_path, 'wb') as f:
      f.write(file_contents.encode('utf-8'))
    if path.endswith('.pdf'):
      return calc_file_hash(file_path)
    else:
      return calc_page_hash(file_path, driver)
  finally:
     os.remove(file_path)
