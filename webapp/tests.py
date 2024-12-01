from django.http import JsonResponse

def popular_keywords_view(request):
    keywords = get_popular_keywords()
    return JsonResponse({"keywords": keywords})