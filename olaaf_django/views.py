import re

from django.http import Http404, HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import get_repo_info
from .authentication import check_authenticity
from .models import Publication

URL_RE = re.compile(
    r'\/(?P<date>([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])))(?P<url>(\/.*))?')


@csrf_exempt
@require_http_methods(['POST'])
def authenticate(request):
  url = request.POST.get('url')

  try:
    repo_name, content_type = get_repo_info(request.get_host(), url)
    publication = Publication.for_partner(repo_name).by_name_or_latest()
  except Publication.DoesNotExist:
    raise Http404()

  date = None
  if 'date' in url:
    url = url.split('date')[1]
    match = URL_RE.match(url)
    date = match.group('date')
    url = match.group('url')

  content = request.POST.get('content')
  if content is None:
    content = request.FILES['content'].file.getvalue()
  auth_response = check_authenticity(publication, date, url, content)
  template = loader.get_template('olaaf_django/response.html')
  context = {
      'auth_response': auth_response
  }
  resp = template.render(context, request)
  response = HttpResponse(resp)
  # addresses the CORS issue
  # robably not the best good solution, but allows development
  response["Access-Control-Allow-Origin"] = "*"
  return response
