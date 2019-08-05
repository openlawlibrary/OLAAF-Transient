import hashlib
from lxml import etree as et
import os
import html

hasher = hashlib.sha256

def calc_file_hash(file_path):
  content = open(file_path, 'rb').read()
  return calc_binary_content_hash(content)

def calc_binary_content_hash(content):
  return hasher(content).hexdigest()

def calc_page_hash(file_path, driver):
  file_path = os.path.abspath(file_path)
  driver.get(f'file://{file_path}')
  page_source = driver.page_source
  # unescape page source
  page_source = html.unescape(page_source)
  doc = et.fromstring(page_source, et.HTMLParser())
  body_section = doc.xpath(".//*[contains(@class, 'tuf-authenticate')]")
  if body_section:
    return hasher(et.tostring(body_section[0])).hexdigest()
  return None

def strip_binary_content(content):
  """
  git show removes an empty line at the end of files, meaning that hash inserted into the database
  is calculated based on content which does not have that new line.
  So, it is necessary to remove it from the provided binary content before calculating its hash.
  surrogateescape is an error handler used to cope with encoding problems.
  """
  return content.decode('utf-8', 'surrogateescape').strip().encode('utf-8', 'surrogateescape')
