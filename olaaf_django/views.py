from .authentication import check_authenticity, AuthetnicationResponse
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template import loader


@csrf_exempt
@require_http_methods(['POST'])
def authenticate(request):
  url = request.POST.get('url')
  content = request.POST.get('content')
  if content is None:
    content = request.FILES['content'].file.getvalue()
  auth_response = check_authenticity(url, content)
  template = loader.get_template('olaaf_django/response.html')
  context = {
    'auth_response': auth_response
  }
  resp = template.render(context, request)
  print(resp)
  return HttpResponse(resp)
