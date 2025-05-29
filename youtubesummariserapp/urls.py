from django.urls import path
from . import views

urlpatterns=[
path("",views.index,name="index"),
    path('summarize/', views.summarize_video, name='summarize_video'),


]
