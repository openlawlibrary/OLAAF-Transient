from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .authentication import check_pdf_authenticity, check_html_authenticity


@csrf_exempt
@require_http_methods(['POST'])
def authenticate(request):
  url = request.POST.get('url')
  if url.endswith('.pdf'):
    pdf = request.FILES['pdf']
    return HttpResponse(check_pdf_authenticity(pdf, url))
  print(url)
  content = request.POST.get('content')
  return HttpResponse(check_html_authenticity(content, url))
