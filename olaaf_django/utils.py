import hashlib
from lxml import etree as et
import html

hasher = hashlib.sha256


def calc_hash(content):
  return hasher(content).hexdigest()

def calc_file_hash(file_path):
  content = open(file_path, 'rb').read()
  return calc_hash(content)

def get_html_document(page_source):
  # unescape page source
  page_source = html.unescape(page_source)
  return et.fromstring(page_source, et.HTMLParser())

def get_auth_div_content(doc):
  auth_div = doc.xpath(".//*[contains(@class, 'tuf-authenticate')]")
  if auth_div:
    return auth_div[0]
  return None

def strip_binary_content(content):
  """
  git show removes an empty line at the end of files, meaning that hash inserted into the database
  is calculated based on content which does not have that new line.
  So, it is necessary to remove it from the provided binary content before calculating its hash.
  surrogateescape is an error handler used to cope with encoding problems.
  """
  return content.decode('utf-8', 'surrogateescape').strip().encode('utf-8', 'surrogateescape')
