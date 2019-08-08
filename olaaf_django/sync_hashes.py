import os
import tempfile
import uuid
from django.db.models import Q
from django.db import transaction
from git import Repo
from datetime import datetime
from selenium import webdriver
from pathlib import Path
from urllib.parse import urlparse
from lxml import etree as et
from olaaf_django.models import Commit, Hash, Edition, Repository
from olaaf_django.utils import calc_hash, get_auth_div_content, get_html_document


options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(chrome_options=options)

EMPTY_TREE_SHA = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
# currently supported file types
SUPPORTED_TYPES = ['html', 'pdf']

def sync_hashes(repo_path):
  """
  Given a path of a html repository, traverse through all commits which
  have not yet been inserted into the database and insert them. For each commit,
  calculate hashes of all new/modified files and calculates hashes of added files.
  Update previously calculated hashes of modified and deleted files and set their
  valid until date.
  Editions are not supported at the moment.
  """

  repo_path = Path(repo_path)
  repo_name = '{}/{}'.format(repo_path.parent.name, repo_path.name)
  repo = Repo(str(repo_path))
  repo_commits = list(repo.iter_commits('master'))[::-1]

  # TODO we need to know when an edition ends and where it begins
  # since editions are on branches, maybe use them
  # or call this edition by edition

  repository, created = Repository.objects.get_or_create(name=repo_name)
  edition = None
  if not created:
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
    # TODO
    # We should not use commit date here since it has not been authenticated
    # The date could be a part of the information passed to sync_hashes, see issue #2
    # Since this is going to be changed soon, not making an effort to check if that date
    # already exists. We have not yet implemented anything that would be affected by the
    # missing counter
    date = datetime.utcfromtimestamp(commit.committed_date).date()
    current_commit = Commit(edition=edition, sha=commit.hexsha, date=date)
    _insert_diff_hashes(repo, prev_commit, current_commit)
    prev_commit = current_commit


def _insert_diff_hashes(repo, prev_commit, current_commit):

  print('Inserting diff hashes. Previous commit {} current commit {}'.format(prev_commit,
                                                                             current_commit))
  diff = repo.git.diff('--name-status', prev_commit.sha, current_commit.sha)
  diff_names = diff.split('\n')
  new_hashes = []
  query = None
  for changed_file in diff_names:
    # git diff contains list of entries in the form of
    # M/A/D file_path
    action, file_path = changed_file.split(maxsplit=1)
    file_path = Path(file_path)
    file_type = file_path.suffix.strip('.')

    if file_type not in SUPPORTED_TYPES:
      continue

    # load file at revision
    posix_path = file_path.as_posix()

    # read content of the file at the current revision, unless that files was
    # just deleted
    # if a html file was deleted, we still need to load it in order to
    # get content of the url property
    # use the previous commit in that case
    git_commit = None
    if action != 'D':
      git_commit = current_commit
    elif file_type == 'html':
      git_commit = prev_commit

    if git_commit is not None:
      file_content = repo.git.show('{}:{}'.format(git_commit.sha, posix_path))
      file_content = file_content.encode('utf-8', 'surrogateescape')

    # if file was added or modified, calculate the new hash
    url = None
    if file_type == 'html':
      doc = _get_document(file_content)
      # try to get url based on content of the url property
      meta_url = doc.xpath(".//*[contains(@property, 'og:url')]")
      if meta_url:
        url = meta_url[0].get('content')
        url = urlparse(url).path
    if url is None:
      url = _calculate_html_url('/' + posix_path)

    # if file aready existed and it was modified or deleted update previous hash
    if action != 'A':
      q = Q(path=url, end_commit__isnull=True)
      if query is None:
        query = q
      else:
        query = query | q

    if action != 'D':
      if file_type == 'html':
        auth_div = get_auth_div_content(doc)
        if auth_div is not None:
          rendered_hash = calc_hash(et.tostring(auth_div))
          search_path = doc.xpath('.//@data-search-path')[-1]
          h = Hash(value=rendered_hash, path=url, hash_type=Hash.RENDERED, search_path=search_path)
          new_hashes.append(h)
      # calculate bitstream hash
      hash_value = calc_hash(file_content)
      h = Hash(value=hash_value, path=url, hash_type=Hash.BITSTREAM)
      new_hashes.append(h)

  def update_hash(h):
    h.end_commit = current_commit
    return h

  with transaction.atomic():
    current_commit.save()
    if len(new_hashes):
      for h in new_hashes:
        h.start_commit = current_commit
      # if a document was changed, but nothing inside the tuf-authenticate
      # div was changed, hash value will remain the same as before, thus
      # breaking the path, value unique constraint
      # TODO see which hashes couldn't be inserted and don't update the old hashes
      Hash.objects.bulk_create(new_hashes, ignore_conflicts=True)

    if query is not None:
      hashes_to_update = Hash.objects.filter(query).iterator()  # default batch size 2000
      hashes_pending_update = (update_hash(h) for h in hashes_to_update)
      Hash.objects.bulk_update(hashes_pending_update, ['end_commit'], batch_size=2000)


def _get_document(file_content):
  temp_dir = Path(tempfile.gettempdir())
  # the file must have .html extension
  # if that is not the case, the browser will not open it correctly
  file_path = (temp_dir / (str(uuid.uuid4()) + '.html')).resolve()
  try:
    with open(str(file_path), 'wb') as f:
      f.write(file_content)
    driver.get(f'file://{file_path}')
    page_source = driver.page_source
    return get_html_document(page_source)
  finally:
    file_path.unlink()


def _calculate_html_url(path):
  if 'index.html' in path:
    url = path.split('index.html')[0]
    if url:
      return url.rsplit('/', 1)[0]
  return path.rsplit('.', 1)[0]
