
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def mobile_app_view(request):
    return render(request, 'mobile/index.html')

def manifest_view(request):
    return JsonResponse({
        "name": "WFM Pro Mobile",
        "short_name": "WFM Pro",
        "start_url": "/mobile/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#1e293b",
        "icons": [
            {
                "src": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/icons/robot.svg",
                "sizes": "192x192",
                "type": "image/svg+xml"
            }
        ]
    })
