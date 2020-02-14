from django.urls import path
from . import views

app_name = 'students'
urlpatterns = [
    path('query/', views.query, name='query'),
]