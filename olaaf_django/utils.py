import datetime as dt
import hashlib
import html

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


URL_PREFIX = lambda date, doc=None: f'/_date/{date}' if doc is None else f'/_date/{date}/_doc/{doc}'  # noqa

def reset_local_urls(html_doc_str, date, doc=None):
  """
  Remove `/_api/_date/<date>/_doc/<doc>` from all absolute local urls in the html document.
  """
  return html_doc_str.replace(URL_PREFIX(date, doc), '')
