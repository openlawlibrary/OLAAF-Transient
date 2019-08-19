import mimetypes
from lxml import etree as et
from .models import Hash, Commit
from .utils import calc_hash, strip_binary_content, get_html_document, \
  get_auth_div_content

# TODO we need to store the information about which edition the document
# belongs to (and to which repository that edition belongs to)

def check_authenticity(url, content):
  if not url.startswith('/'):
    url = '/' + url
  content_type, _ = mimetypes.guess_type(url)
  file_type = content_type.split('/')[1] if content_type is not None else 'html'
  hashing_func = {
    'html': _calculate_html_hash,
    'pdf': _calculate_binary_content_hash
  }.get(file_type)

  if hashing_func is None:
    return AuthetnicationResponse(url, authenticable=False)

  hash_value = hashing_func(content)
  try:
    hash_type = Hash.RENDERED if file_type == 'html' else Hash.BITSTREAM
    hash_obj = Hash.objects.get(path__url=url, value=hash_value, hash_type=hash_type)
    start_commit_date = Commit.objects.get(id=hash_obj.start_commit.id).date
    if hash_obj.end_commit is None:
      return AuthetnicationResponse(url, authentic=True, current=True, from_date=start_commit_date)
    else:
      end_commit_date = Commit.objects.get(id=hash_obj.end_commit.id).date
      return AuthetnicationResponse(url, authentic=True, from_date=start_commit_date,
                                    to_date=end_commit_date)
  except Hash.DoesNotExist:
    # not authentic
    return AuthetnicationResponse(url)

def _calculate_binary_content_hash(binary_content):
  binary_content = strip_binary_content(binary_content)
  return calc_hash(binary_content)

def _calculate_html_hash(html_content):
  doc = get_html_document(html_content)
  body_section = get_auth_div_content(doc)
  return calc_hash(et.tostring(body_section))

class AuthetnicationResponse():

  def __init__(self, url, authenticable=True, authentic=False, current=False, from_date=None,
               to_date=None):
    self.authenticable = authenticable
    self.authentic = authentic
    self.current = current
    self.from_date = from_date
    self.to_date = to_date
    self.url = url
