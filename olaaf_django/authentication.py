import mimetypes
import datetime
from lxml import etree as et

from .models import Hash, Publication
from .utils import (calc_hash, get_auth_div_content, get_html_document,
                    strip_binary_content)

# TODO we need to store the information about which publication the document
# belongs to (and to which repository that publication belongs to)


def check_authenticity(date, url, content):
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
  publication = Publication.objects.order_by('-name')[0]

  if date is not None:
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

  hash_type = Hash.RENDERED if file_type == 'html' else Hash.BITSTREAM
  hash_data = Hash.objects.filter(path__url=url, value=hash_value, hash_type=hash_type,
                                  start_commit__publication=publication). \
                                  values('start_commit__date', 'end_commit__date')

  if not len(hash_data):
    # not authentic
    return AuthetnicationResponse(url, date=date)

  start_commit_date = hash_data[0]['start_commit__date']
  end_commit_date = hash_data[0]['end_commit__date']

  if date is None:
    if end_commit_date is None:
      return AuthetnicationResponse(url, authentic=True, current=True, from_date=start_commit_date)
    else:
      return AuthetnicationResponse(url, authentic=True, from_date=start_commit_date,
                                    to_date=end_commit_date)

  if date >= start_commit_date and (end_commit_date is None or date <= end_commit_date):
    return AuthetnicationResponse(url, authentic=True, from_date=start_commit_date, date=date)
  else:
    return AuthetnicationResponse(url, authentic=False, date=date)


def _calculate_binary_content_hash(binary_content):
  binary_content = strip_binary_content(binary_content)
  return calc_hash(binary_content)


def _calculate_html_hash(html_content):
  doc = get_html_document(html_content)
  body_section = get_auth_div_content(doc)
  return calc_hash(et.tostring(body_section))


class AuthetnicationResponse():

  def __init__(self, url, authenticable=True, authentic=False, current=False, from_date=None,
               to_date=None, date=None):
    self.authenticable = authenticable
    self.authentic = authentic
    self.current = current
    self.from_date = from_date
    self.to_date = to_date
    self.url = url
    self.date = date
