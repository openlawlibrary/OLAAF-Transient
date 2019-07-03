import hashlib
from lxml import etree as et
import os

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
  doc = et.fromstring(page_source, et.HTMLParser())
  body_section = doc.xpath(".//section[@class='col8 body']")
  if body_section:
    return hasher(et.tostring(body_section[0])).hexdigest()
  return None
