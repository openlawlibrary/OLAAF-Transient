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

  if len(inserted_commits) == 0:
    init_commit = _insert_hashes_initial(repo, repo_commits[0], edition)
    inserted_commits.append(init_commit)

  # find the last inserted commit
  inserted_commits_num = len(inserted_commits)
  prev_commit = inserted_commits[-1]
  for commit in repo_commits[inserted_commits_num::]:
    date = datetime.utcfromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M')
    current_commit = Commit(edition=edition, sha=commit.hexsha, date=date)
    current_commit.save()
    _insert_diff_hashes(repo, prev_commit, current_commit)
    prev_commit = current_commit

  repo.git.checkout('master')


def _insert_hashes_initial(repo, commit, edition):
  '''
  Calculates and inserts hashes by traversing through all files in the repository
  '''
  repo.git.checkout(commit)
  date = datetime.utcfromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M')
  commit = Commit(sha=commit.hexsha, date=date, edition=edition)
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
          path = path.rsplit('.', 1)[0]
          if hash_value is not None:
            h = Hash(value=hash_value, path=path, start_commit=commit)
            h.save()
  return commit

def post_merge_add_hashes(repo_path):
  repo_path = Path(repo_path)
  repo_name = '{}/{}'.format(repo_path.parent.name, repo_path.name)

  repository = Repository.objects.filter(name=repo_name).first()
  if repository is None:
    print('Repository hashes not initialized')
    return
  # add to the current edition
  edition = Edition.objects.filter(repository=repository).reverse()[0]

  repo = Repo(str(repo_path))
  # find the previous commit 'ORIG_HEAD'
  prev_commit_sha = repo.git.rev_parse('ORIG_HEAD')
  prev_commit = Commit.objects.filter(edition=edition, sha=prev_commit_sha).first()
  if prev_commit is None:
    print('Commit {} not found in the databa.'.format(prev_commit_sha))
    return
  new_commit_sha = repo.git.rev_parse('HEAD')
  commit_date = repo.git.show(s=True, format='%ci {}'.format(new_commit_sha)).split()[0]
  new_commit = Commit(sha=new_commit_sha, date=commit_date, edition=edition)
  new_commit.save()
  _insert_diff_hashes(repo, prev_commit, new_commit)


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
      file_path = os.path.abspath(os.path.join(repo.working_dir, file_name))
      path = file_name.replace(os.sep, '/')
      # remove .html
      path = path.rsplit('.', 1)[0]
      # if file aready existed and it was modified or deleted update previous hash
      if action != 'A':
        previous_hash = Hash.objects.get(path=path, end_commit__isnull=True)
        previous_hash.end_commit = current_commit
        previous_hash.save()
        print('Updated hash for path ' + path)
      # if file was added or modified, calculate the new hash
      if action != 'D':
        repo.git.checkout(current_commit.sha, file_name)
        hash_value = _calculate_file_hash(file_path)
        if hash_value is not None:
          h = Hash(value=hash_value, path=path, start_commit=current_commit)
          h.save()
          print('Create new hash for path ' + path)


def _calculate_file_hash(file_path):
  if file_path.endswith('.pdf'):
    return calc_file_hash(file_path)
  else:
    return calc_page_hash(file_path, driver)
