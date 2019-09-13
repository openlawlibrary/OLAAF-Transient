import pathlib
import tempfile
import uuid
from datetime import datetime
from urllib.parse import urlparse

from django.db import transaction
from django.db.models import Q
from git import Repo
from lxml import etree as et
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from olaaf_django.models import Commit, Hash, Path, Publication, Repository
from olaaf_django.utils import (calc_hash, get_auth_div_content,
                                get_html_document)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(chrome_options=chrome_options)

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(chrome_options=options)

EMPTY_TREE_SHA = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
# currently supported file types
SUPPORTED_TYPES = ['html', 'pdf']
MAX_QUERIES = 500


def sync_hashes(repo_path):
  """
  Given a path of an html repository, gets the publication branches and
  traverse through all its commits which have not yet been inserted into the
  database and insert them. For each commit, calculate hashes of all
  new/modified files and calculates hashes of added files. Update previously
  calculated hashes of modified and deleted files and set their valid until
  date.
  """

  repo_path = pathlib.Path(repo_path)
  repo_name = '{}/{}'.format(repo_path.parent.name, repo_path.name)
  repo = Repo(str(repo_path))

  repository, _ = Repository.objects.get_or_create(name=repo_name)

  # Call sync hashes for all publications
  for pub_branch in filter(lambda b: b.name.startswith('publication/'), repo.branches):
    publication_commits = list(repo.iter_commits(pub_branch, reverse=True))

    commit_date = repo.git.show(s=True, format=f'%ci {publication_commits[0].hexsha}').split()[0]
    release, _ = Publication.objects.get_or_create(repository=repository,
                                                   name=pub_branch.name.strip('publication/'),
                                                   date=commit_date)
    _sync_hashes_for_publication(repo, release, publication_commits)


def _sync_hashes_for_publication(repo, publication, publication_commits):
  # check if commits are already in the database
  # if they are, see if there are commits which have not been inserted yet
  # if not, insert the hashes from the beginning
  inserted_commits = Commit.objects.filter(publication=publication)[::1]
  if len(inserted_commits) == len(publication_commits):
    print('All commits have been loaded into the database')
    return

  # find the last inserted commit
  inserted_commits_num = len(inserted_commits)
  if inserted_commits_num == 0:
    prev_commit = Commit(sha=EMPTY_TREE_SHA)
  else:
    prev_commit = inserted_commits[-1]

  for commit in publication_commits[inserted_commits_num::]:
    # TODO
    # We should not use commit date here since it has not been authenticated
    # The date could be a part of the information passed to sync_hashes, see issue #2
    # Since this is going to be changed soon, not making an effort to check if that date
    # already exists. We have not yet implemented anything that would be affected by the
    # missing counter
    date = datetime.utcfromtimestamp(commit.committed_date).date()
    current_commit = Commit(publication=publication, sha=commit.hexsha, date=date)
    _insert_diff_hashes(publication, repo, prev_commit, current_commit)
    prev_commit = current_commit


def _insert_diff_hashes(publication, repo, prev_commit, current_commit):
  """
  <Purpose>
    Inserts and updates hashes for each document that was added, modified
    or deleted in the specified commit `current_commit`. Uses git diff
    to find the difference between previous commit `prev_commit` and `current_commit`.
  <Arguments>
    publication:
      Publication to which the inserted hashes belong
    repo:
      Git repository whose commits and hashes and being inserted into the database
    prev_commit:
      Previous commit, which was already inserted into the database, or emtpy tree sha
      if there is no previous commit
    current_commit:
      The current commit
  """

  print('Inserting diff hashes. Previous commit {} current commit {}'.format(prev_commit,
                                                                             current_commit))

  # keep track of paths of new files
  # these path have to be inserted into the database
  added_files_paths = []
  # query hashes which were updated or deleted
  # in case of some databases (e.g. sqlite which is used for testing) iterator raises an
  # exception if there are over 1000 results
  # so, we need to separate one big query into multiple smaller one
  hashes_queries = []
  current_query = None
  current_query_length = 0
  doc = None
  # a dictionary which maps path, type tuples to hashes
  hashes_by_paths_and_types = {}
  # keep track of new hashes which should be inserted into the database
  new_hashes = []

  diff = repo.git.diff('--name-status', prev_commit.sha, current_commit.sha)
  diff_names = diff.split('\n')

  for changed_file in diff_names:
    # git diff contains list of entries in the form of
    # M/A/D file_path
    action, file_path = changed_file.split(maxsplit=1)
    file_path = pathlib.Path(file_path)
    file_type = file_path.suffix.strip('.')
    if file_type not in SUPPORTED_TYPES:
      continue

    path_parts = file_path.parts[:-1]
    if any((path_part[0] in ('_', '.') for path_part in path_parts)):
      continue

    posix_path = file_path.as_posix()

    # Unless the file was deleted, we need to read its content in order to calculate
    # its hash(es) and, if the file is an html file which was added, to read its url
    if action != 'D':
      file_content, doc = _get_file_content_and_document(repo, current_commit.sha,
                                                         posix_path, file_type)

    if action == 'A':
      # If a new file was added, create a new path object. Calculating url here might be unnecessary
      # (in cases when the path already exists), but it's probably better to do that than to have
      # to store doc object to be used later. It is probably far more likely that the path
      # will have to be created than not
      url = _get_url(posix_path, file_type, doc)
      try:
        search_path = doc.xpath('.//@data-search-path')[-1] if doc is not None else None
      except IndexError:
        search_path = None

      added_files_paths.append({'filesystem': posix_path, 'url': url, 'publication': publication,
                                'search_path': search_path})
    else:
      # If the file was modified or deleted, it is necessary to update its latest hash
      hash_query = Q(path__filesystem=posix_path, end_commit__isnull=True)
      if not current_query_length:
        current_query = hash_query
        current_query_length = 1
      else:
        current_query = current_query | hash_query

      if current_query_length == MAX_QUERIES:
        hashes_queries.append(current_query)
        current_query = None
        current_query_length = 0
      else:
        current_query_length += 1

    if action != 'D':
      bitstream_hash, rendered_hash = _calculate_file_hashes(
          file_content, doc)
      hashes_by_paths_and_types[(
          posix_path, Hash.BITSTREAM)] = bitstream_hash
      if rendered_hash is not None:
        hashes_by_paths_and_types[(
            posix_path, Hash.RENDERED)] = rendered_hash

  if current_query is not None:
    hashes_queries.append(current_query)

  _add_and_update_paths_and_hashes(current_commit, hashes_queries, hashes_by_paths_and_types,
                                   added_files_paths)


@transaction.atomic
def _add_and_update_paths_and_hashes(current_commit, hashes_queries, hashes_by_paths_and_types,
                                     added_files_paths):
  """
  <Purpose>
    Inserts the current commit and all new paths and hashes into the database. Modifies
    hashes of updated and deleted files. Decorator transaction.atomic guarantees atomicity.
  <Arguments>
    current_commit:
      Current repo commit. Added hashes will have that commit as their start commit. In case
      of modification and removal of files, this commit will be set as the end commit of the
      appropriate hashes.
    hashes_queries:
      Django's Q object which combines query statements each of which retrieves one hash
      from the database.
    hashes_by_paths_and_types:
      A dictionary which contains all new hashes which should be inserted into the database.
      These hashes are created either when a new file is added at a revision. Keys are
      tuples (filesystem_path, hash_type). Values are hash objects.
    added_files_paths:
      A list of dictionaries, where each dictionary contains information of one path object
      which is to be inserted into the database.
  """
  current_commit.save()

  if len(hashes_queries):
    # find all hashes which were modified or deleted

    def _get_hashes_pending_update():
      for hashes_query in hashes_queries:
        hashes_to_update = Hash.objects.filter(hashes_query).iterator()
        for h in hashes_to_update:
          path_and_hash = (h.path.filesystem, h.hash_type)
          new_hash = hashes_by_paths_and_types.get(path_and_hash)
          if new_hash is not None:
            # hash was modified
            if new_hash.value == h.value:
              # do not update the existing hash and insert a new one if it remained unchanged
              # this can only happen in case of rendered hashes
              del hashes_by_paths_and_types[path_and_hash]
            else:
              new_hash.path = h.path
              new_hash.start_commit = current_commit
              h.end_commit = current_commit
              yield h
          else:
            # file deleted
            h.end_commit = current_commit
            yield h

    Hash.objects.bulk_update(_get_hashes_pending_update(), ['end_commit'], batch_size=2000)

  if added_files_paths:
    for path in added_files_paths:
      # when inside a transaction, this should also be executed in batches
      # see https://stackoverflow.com/questions/3395236/aggregating-saves-in-django
      db_path, _ = Path.objects.get_or_create(**path)
      for hash_type in (Hash.RENDERED, Hash.BITSTREAM):
        h = hashes_by_paths_and_types.get((db_path.filesystem, hash_type))
        if h is not None:
          h.path = db_path
          h.start_commit = current_commit

  # insert all new hashes (corresponding to both new and modified files) into the database
  Hash.objects.bulk_create(hashes_by_paths_and_types.values())


def _calculate_file_hashes(file_content, doc):
  """
  <Purpose>
    Calculate bitstream and rendered hash of a file
  <Arguments>
    file_content:
      Full content of the file
    doc:
      lxml document corresponding to the file (if the file is an html file)
  <Returns>
    bitstream hash, rendered hash
  """
  # calculate bitstream hash
  hash_value = calc_hash(file_content)
  bitstream_hash = Hash(value=hash_value, hash_type=Hash.BITSTREAM)

  rendered_hash = None
  if doc is not None:
    # this is an html file, calculate its rendered hash
    auth_div = get_auth_div_content(doc)
    if auth_div is not None:
      rendered_hash_value = calc_hash(et.tostring(auth_div))
      rendered_hash = Hash(value=rendered_hash_value, hash_type=Hash.RENDERED)

  return bitstream_hash, rendered_hash


def _calculate_html_url(path):
  """
  <Purpose>
    Calculate URL of an html file which does not have a org:url property based on its
    filesystem path.
  <Arguments>
    path:
      filesystem path of an html file
  <Returns>
    Calculated URL
  """
  if 'index.html' in path:
    url = path.split('index.html')[0]
    if url:
      return url.rsplit('/', 1)[0]
  return path.rsplit('.', 1)[0]


def _get_file_content_and_document(repo, commit_sha, file_path, file_type):
  """
  <Purpose>
    Read content of a file at a given revision. If that file is an html file,
    also return lxml document object corresponding to that file
  <Arguments>
    repo:
      Git repository
    commit_sha:
      Commit SHA indicating at which revision to load content of the specified file
    file_path:
      Path of the file which is to be read in Unix style. Relative to the root of the
      git repository
    <Returns>
      (file content, lxml document)
  """
  file_content = repo.git.show('{}:{}'.format(commit_sha, file_path))
  file_content = file_content.strip().encode('utf-8', 'surrogateescape')

  doc = None
  if file_type == 'html':
    # If the file is an html file, get the document object so that it's possible to find
    # elements such as authentication div, search path and url
    doc = _get_document(file_content)

  return file_content, doc


def _get_document(file_content):
  """
  <Purpose>
    Creates an lxml document object given content of an html file.
    Since browsers might modify html files in order to properly show them,
    we use chrome web driver to open an html document, get the page source,
    and create an lxml document given that page source.
  <Arguments>
    file_content:
      Content of an html file
  <Returns>
    lxml document object
  """
  temp_dir = pathlib.Path(tempfile.gettempdir())
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


def _get_url(path, file_type, doc):
  """
  <Purpose>
    Get URL of the given document. If the document is an html document, try to
    read its og:url property. If there is no such property or if the document
    if of a different type, calculate its URL based on its filesystem path.
  <Arguments>
    path:
      Filesystem path of the file
    file_type:
      File's type
    doc:
      lxml document object. None if the file_type is not html
  <Returns>
    URL of the file with the given filesystem path
  """
  url = '/' + path
  if file_type != 'html':
    return url

  # try to get url based on content of the url property
  meta_url = doc.xpath(".//*[contains(@property, 'og:url')]")
  if meta_url is not None and len(meta_url):
    url = meta_url[0].get('content')
    url = urlparse(url).path
  else:
    url = _calculate_html_url(url)
  return url
