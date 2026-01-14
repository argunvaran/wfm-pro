
from django.urls import path
from .views import import_data, download_sample_csv

urlpatterns = [
    path('', import_data, name='import_data'),
    path('sample/<str:type>/', download_sample_csv, name='download_sample_csv'),
]
