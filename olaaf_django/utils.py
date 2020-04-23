import datetime as dt
import hashlib
import html
import time
from functools import wraps

from lxml import etree as et

hasher = hashlib.sha256


def calc_hash(content):
  """
  <Purpose>
    Calculate sha-256 hash of the provided binary string
  <Arguments>
    content:
      Binary string whose hash will be calculated
  <Returns>
    sha-256 hash of the input
  """
  return hasher(content).hexdigest()


def calc_file_hash(file_path):
  """
  <Purpose>
    Calculate sha-256 hash of a file with at the provided path
  <Arguments>
    file_path:
      Path to file whose hash will be calculated
  <Returns>
    sha-256 hash of content of a file at the provided path
  """
  content = open(file_path, 'rb').read()
  return calc_hash(content)


def get_html_document(page_source):
  """
  <Purpose>
    Create and return lxml document given its content
  <Arguments>
    page_source:
      Document content
  <Returs>
    Created lxml document
  """
  # unescape page source
  page_source = html.unescape(page_source)
  return et.fromstring(page_source, et.HTMLParser())


def get_auth_div_content(doc):
  """
  <Purpose>
    Get div which contains class tuf-authetnicate belonging to the provided document
  <Arguments>
    doc:
      An lxml document
    <Returns>
      div lxml element with class tuf-authenticate if the document contains it, None otherwise
  """
  auth_div = doc.xpath(".//*[contains(@class, 'tuf-authenticate')]")
  if auth_div:
    return auth_div[0]
  return None


def strip_binary_content(content):
  """
  <Purpose>
    Git show removes an empty line at the end of files, meaning that hash inserted into the database
    is calculated based on content which does not have that new line.
    So, it is necessary to remove it from the provided binary content before calculating its hash.
    surrogateescape is an error handler used to cope with encoding problems.
  <Arguments>
    contents:
       binary string from which leading and trailing whitespaces should be stripped
  <Returns>
    Stripped content
  """
  return content.decode('utf-8', 'surrogateescape').strip().encode('utf-8', 'surrogateescape')


def is_iso_date(date):
  """Check if input date is a valid iso date.
  """
  try:
    dt.datetime.strptime(date, '%Y-%m-%d').date().isoformat()
    return True
  except ValueError:
    return False


def remove_endings(input_str, endings=('index.html', 'index.full.html', '.full.html', '.html', '.htm')):
  """Removes `endings` from string if exists."""
  for ending in endings:
    if input_str.endswith(ending):
      input_str = input_str[:-len(ending)]
  return input_str


class timed_run:
  """Decorator to let us capture the elapsed time and optionally print a timer and start/end
     messages around function calls"""

  def __init__(self, start_message=None, end_message='  completed in {} seconds'):
    self.start_message = start_message
    self.end_message = end_message
    self.start_time = None
    self.elapsed_time = None

  def start(self):
    self.start_time = time.time()
    if self.start_message is not None:
      print()
      print(self.start_message)

  def end(self):
    self.elapsed_time = time.time() - self.start_time
    if self.end_message is not None:
      print()
      print(self.end_message.format(int(self.elapsed_time)))

  def __call__(self, orig_func=None):
    @wraps(orig_func)
    def wrapper_func(*args, **kwargs):
      self.start()
      result = orig_func(*args, **kwargs) if orig_func else None
      self.end()
      return result
    return wrapper_func


def URL_PREFIX(pub_name, date, doc=None):
  pub_part = f'/_publication/{pub_name}' if pub_name else ''
  date_part = f'/_date/{date}' if date else ''
  doc_part = f'/_doc/{doc}' if doc else ''

  return f'{pub_part}{date_part}{doc_part}'


def reset_local_urls(html_doc_str, pub_name, date, doc=None):
  """
  Remove `/_api/_date/<date>/_doc/<doc>` from all absolute local urls in the html document.
  """
  return html_doc_str.replace(URL_PREFIX(pub_name, date, doc), '')
