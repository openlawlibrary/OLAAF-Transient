import datetime
import mimetypes

from django.http import HttpResponse
from django.template import loader
from lxml import html as et_html

from .models import Hash, Path, Publication
from .utils import (calc_hash, get_auth_div_content, get_html_document,
                    reset_local_urls)

HTML_CONTENT_TYPE = mimetypes.types_map.get('.html')
PDF_CONTENT_TYPE = mimetypes.types_map.get('.pdf')


def check_authenticity(publication, pub_name, date, path, url, content, content_type):
  hashing_func = {
      HTML_CONTENT_TYPE: _calculate_html_hash,
      PDF_CONTENT_TYPE: _calculate_binary_content_hash
  }.get(content_type)

  if hashing_func is None or not _is_authenticable(publication, path):
    return AuthenticationResponse(url, authenticable=False)

  if content_type == HTML_CONTENT_TYPE:
    content = reset_local_urls(content, pub_name, date)

  try:
    hash_value = hashing_func(content, content_type)
  except Exception:
    return AuthenticationResponse(url, authenticable=False)

  if date is not None:
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

  hash_type = Hash.RENDERED if content_type == HTML_CONTENT_TYPE else Hash.BITSTREAM
  hash_data = (
      Hash.objects
      .filter(
          path__url=path,
          value=hash_value,
          hash_type=hash_type,
          start_commit__publication=publication)
      .values('start_commit__date', 'end_commit__date')
  )

  if not len(hash_data):
    # not authentic
    return AuthenticationResponse(url, date=date)

  start_commit_date = hash_data[0]['start_commit__date']
  end_commit_date = hash_data[0]['end_commit__date']

  if date is None:
    if publication.name == publication.latest and end_commit_date is None:
      return AuthenticationResponse(url, authentic=True, current=True, from_date=start_commit_date)
    else:
      return AuthenticationResponse(url, authentic=True, from_date=start_commit_date,
                                    to_date=end_commit_date)

  if date >= start_commit_date and (end_commit_date is None or date <= end_commit_date):
    return AuthenticationResponse(url, authentic=True, from_date=start_commit_date, date=date)
  else:
    return AuthenticationResponse(url, authentic=False, date=date)


def _is_authenticable(publication, path):
  return Path.objects.filter(publication=publication, url=path).count() > 0


def _calculate_binary_content_hash(binary_content, file_type):
  return calc_hash(binary_content, file_type)


def _calculate_html_hash(html_content, file_type):
  doc = get_html_document(html_content)
  body_section = get_auth_div_content(doc)
  return calc_hash(et_html.tostring(body_section, encoding="utf-8"), file_type)


class AuthenticationResponse:
  def __init__(self, url, authenticable=True, authentic=False, current=False, from_date=None,
               to_date=None, date=None, link=None):
    self.authenticable = authenticable
    self.authentic = authentic
    self.current = current
    self.from_date = from_date
    self.to_date = to_date
    self.url = url
    self.date = date

  def to_http_response(self, request):
    template = loader.get_template('olaaf_django/response.html')
    context = {
        'auth_response': self
    }
    resp = template.render(context, request)
    response = HttpResponse(resp)
    # addresses the CORS issue
    # probably not the best solution, but allows development
    response["Access-Control-Allow-Origin"] = "*"
    return response
