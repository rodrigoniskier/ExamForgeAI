from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.core.cache import cache


def context(request):
    return {"portfolio_demo": settings.PORTFOLIO_DEMO, "demo_accounts": settings.DEMO_ACCOUNTS}

@require_POST
def enter(request):
    if not settings.PORTFOLIO_DEMO:
        raise Http404
    name = request.POST.get("account", "")
    if name not in dict(settings.DEMO_ACCOUNTS):
        raise Http404
    try:
        user = User.objects.get(username=name, is_active=True, is_staff=False, is_superuser=False)
    except User.DoesNotExist:
        return HttpResponse("Demonstração em preparação.", status=503)
    request.session.flush()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("dashboard")

def health(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status":"ok", "demo":settings.PORTFOLIO_DEMO})

class DemoSafetyMiddleware:
    def __init__(self, get_response): self.get_response=get_response
    def __call__(self, request):
        if settings.PORTFOLIO_DEMO:
            if request.path.startswith(("/admin/", "/import/")):
                return HttpResponse("Recurso indisponível na demonstração.", status=403)
            if request.method in ("DELETE", "PUT", "PATCH") or request.FILES:
                return HttpResponse("Operação indisponível na demonstração.", status=403)
            if request.method == "POST" and request.path not in ("/demo/enter/", "/logout/"):
                used = request.session.get("demo_actions", 0)
                if used >= 30:
                    return HttpResponse("Limite desta sessão atingido. Entre novamente para explorar.", status=429)
                request.session["demo_actions"] = used + 1
        response = self.get_response(request)
        response["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
        response["Content-Security-Policy"]="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        return response
