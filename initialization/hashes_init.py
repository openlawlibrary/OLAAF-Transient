import os
import posixpath
from git import Repo
from datetime import datetime
from selenium import webdriver
from django.core.wsgi import get_wsgi_application
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authsite.settings")
application = get_wsgi_application()

from transient_auth.models import Commit, Hash, Edition, Repository
from transient_auth.utils import calc_file_hash, calc_page_hash

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(chrome_options=options)

def initialize_hashes(repo_path, initial_commit=None):
  repo_path = Path(repo_path)
  repo_name = '{}/{}'.format(repo_path.parent.name, repo_path.name)
  repo = Repo(str(repo_path))
  commits = list(repo.iter_commits('master'))[::-1]
  if initial_commit is None:
    initial_commit = commits[0]

  commit_date = repo.git.show(s=True, format='%ci {}'.format(initial_commit)).split()[0]

  # check if repository already
  repository = Repository.objects.filter(name=repo_name).first()
  if repository is None:
    repository = Repository(name=repo_name)
    repository.save()
    edition = None
  else:
    # try to find edition by repo name and commit date
    edition = Edition.objects.filter(repository=repository.id, date=commit_date).first()

  if edition is not None:
    create = ('Edition already created. Do you want to delete it and create it again? [y/n]: ')
    if create != 'y':
      return
    edition.delete()

  edition_name = commit_date.rsplit('-', 1)[0]
  edition = Edition(name=edition_name, date=commit_date, repository=repository)
  edition.save()

  hashes_count = Hash.objects.count()
  print(hashes_count)
  if hashes_count > 0:
    print('Hashes already exist. Remove the existing hashes from the database '
          'and execute the command again if necessary')
   #return


  if initial_commit is not None:
    commit_index = None
    for index, commit in enumerate(commits):
      if initial_commit == commit.hexsha:
        commit_index = index
        break
    if commit_index is None:
      print('The specified initial commit does not exist')
      return
    commits = commits[commit_index::]

  _insert_hashes_initial(repo, commits[0])
  commits_count = len(commits)
  previous_commit = Commit.objects.get(sha=commits[0].hexsha)
  for commit in commits[1::]:
    date = datetime.utcfromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M')
    current_commit = Commit.objects.filter(sha=commit.hexsha).first()
    if current_commit is None:
      current_commit = Commit(sha=commit.hexsha, date=date)
      current_commit.save()
    insert_commit_hashes(repo, previous_commit, current_commit)
    previous_commit = current_commit


def _insert_hashes_initial(repo, commit):
  '''
  Calculates and inserts hashes by traversing through all files in the repository
  '''
  repo.git.checkout(commit)
  date = datetime.utcfromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M')
  commit = Commit(sha=commit.hexsha, date=date)
  commit.save()

  for root, directories, filenames in os.walk(repo.working_dir):
    if '.git' not in root:
      # form url based on the file path
      # ensure that windows separators are replaced
      url = os.path.relpath(root, repo.working_dir).replace(os.sep, '/')
      for file_name in filenames:
        if file_name.endswith('.html') or file_name.endswith('.pdf'):
          file_path = os.path.abspath(os.path.join(root, file_name))
          hash_value = _calculate_file_hash(file_path)
          path = posixpath.join(url, file_name)
          if hash_value is not None:
            h = Hash(value=hash_value, path=path, start_commit=commit)
            h.save()


def insert_commit_hashes(repo, prev_commit, current_commit):
  '''
  Calculates and inserts hashes of modified files only
  '''
  print('Inserting commits. Previous commit {} current commit {}'.format(prev_commit, current_commit))
  diff = repo.git.diff('--name-status', prev_commit.sha, current_commit.sha)
  diff_names = diff.split('\n')
  print(len(diff_names))
  for changed_file in diff_names:
    # we do not want to calculate hashes of index pages, images, json files etc.
    if changed_file.endswith('.html') or changed_file.endswith('.pdf'):
      # git diff contains list of entries in the form of
      # M/A file_name.html
      # so remove the modified/added indicator (first letter) and whitespaces
      changed_file = changed_file[1:].strip()
      file_path = os.path.abspath(os.path.join(repo.working_dir, changed_file))
      repo.git.checkout(current_commit.sha, changed_file)
      hash_value = _calculate_file_hash(file_path)
      path = changed_file.replace(os.sep, '/')
      previous_hash = Hash.objects.filter(path=path, start_commit=prev_commit).first()
      if previous_hash is None:
        continue
      previous_hash.end_commit = current_commit
      previous_hash.save()
      if hash_value is not None:
        h = Hash(value=hash_value, path=path, start_commit=current_commit)
        h.save()


def _calculate_file_hash(file_path):
  if file_path.endswith('.pdf'):
    return calc_file_hash(file_path)
  else:
    return calc_page_hash(file_path, driver)
