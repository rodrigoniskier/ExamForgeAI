from django.contrib import admin
from django.urls import include,path
urlpatterns=[path("admin/",admin.site.urls),path("",include("bank.urls"))]

from portfolio_demo import enter, health
urlpatterns += [path("demo/enter/", enter, name="demo_enter"), path("healthz", health)]
