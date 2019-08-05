import hashlib
from lxml import etree as et
from .models import Hash, Commit
from .utils import calc_file_hash, calc_binary_content_hash, strip_binary_content

# TODO we need to store the information about which edition the document
# belongs to (and to which repository that edition belongs to)

def check_pdf_authenticity(pdf_content, url):
  pdf_content = strip_binary_content(pdf_content)
  pdf_hash = calc_binary_content_hash(pdf_content)
  return check_authenticity(pdf_hash, url)

def check_html_authenticity(content, url):
  parser = et.HTMLParser()
  doc = et.fromstring(content, parser)
  body_section = doc.xpath(".//*[contains(@class, 'tuf-authenticate')]")[0]
  file_hash = hashlib.sha256(et.tostring(body_section)).hexdigest()
  return check_authenticity(file_hash, url)


def check_authenticity(file_hash, url):
  path = url[1:]
  hashes = list(Hash.objects.filter(path=path))
  if not len(hashes):
    return 'Cannot authenticate'
  for a_hash in hashes[::-1]:
    if a_hash.value == file_hash:
      start_commit_date = Commit.objects.get(id=a_hash.start_commit.id).date
      if a_hash.end_commit is None:
        return 'Authentic and current.<br/>Valid from {}'.format(start_commit_date)
      else:
        end_commit_date = Commit.objects.get(id=a_hash.end_commit.id).date
        return 'Authentic, but not current.<br/>Valid from {} to {}'.format(start_commit_date,
                                                                            end_commit_date)
  return 'Not authentic'
