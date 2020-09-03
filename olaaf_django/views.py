import json
import re

from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import get_repo_info
from .authentication import AuthenticationResponse, check_authenticity
from .messages import (VALID_CURRENT_DOC_MSG, VALID_OUTDATED_DOC_MSG,
                       format_message)
from .models import Hash, Publication

URL_RE = re.compile(
    r'((\/)?_publication\/(?P<pub>(\d{4}-\d{2}(-\d{2})?(-\d{2})?)))?' +  # backwards compatible
    r'((\/)?_date\/(?P<date>(\d{4}-\d{2}-\d{2})))?' +
    r'(\/)?(?P<path>(.*))'
)


@csrf_exempt
@require_http_methods(['POST'])
def authenticate(request):
  url = request.POST.get('url')

  if not url:
    return AuthenticationResponse(url, authenticable=False).to_http_response(request)

  pub_name, date, path = _extract_url(url)

  try:
    repo_name, content_type = get_repo_info(request.get_host(), path)
    publication = Publication.for_partner(repo_name).by_name_or_latest(pub_name, strict=True)
  except Publication.DoesNotExist:
    raise Http404()

  content = request.POST.get('content')
  if content is None:
    content = request.FILES['content'].file.getvalue()

  auth_response = check_authenticity(publication, pub_name, date, path, url, content, content_type)

  return auth_response.to_http_response(request)


@csrf_exempt
@require_http_methods(['POST'])
def check_hashes(request):
  results = []
  try:
    data = json.loads(request.body)
    for file_info in data:
      file_name = file_info.get('name')
      file_hash = file_info.get('hash')

      authentic = False
      msg = None

      try:
        hash_obj = Hash.objects.get(value=file_hash)

        authentic = True

        start_date = hash_obj.start_commit.date
        if hash_obj.end_commit:
          end_date = hash_obj.end_commit.date
          msg = format_message(VALID_OUTDATED_DOC_MSG,
                               start_date=start_date, end_date=end_date)
        else:
          msg = format_message(VALID_CURRENT_DOC_MSG, start_date=start_date)

      except Hash.DoesNotExist:
        pass
      except Exception as e:
        msg = f'An error ocurred: {e}'

      results.append(dict(
          name=file_name,
          authentic=authentic,
          msg=msg
      ))
  except Exception:
    pass

  return JsonResponse(results, safe=False)


def _extract_url(url):
  """Extract publication name, version (date) and path from url

  e.g.
    _publication/2020-01-10/_date/2018-04-05/us/ca/cities/san-mateo/charter/I
    > 2020-01-10, 2018-04-05, us/ca/cities/san-mateo/charter/I

    _date/2018-04-05/us/ca/cities/san-mateo/charter/I
    > None, 2018-04-05, us/ca/cities/san-mateo/charter/I

    _publication/2020-01-10/us/ca/cities/san-mateo/charter/I
    > 2020-01-10, None, us/ca/cities/san-mateo/charter/I

    all other cases will return
    None, None, url
  """
  try:
    match = URL_RE.match(url)
    return match.group('pub'), match.group('date'), match.group('path')
  except Exception:
    return None, None, None
