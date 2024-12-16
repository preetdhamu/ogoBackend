from home.views import * 
from django.urls import path , include


urlpatterns = [
   path('authorize-user/' , authorizeUser),
   path('upload-video/' , VideoUploadView.as_view() , name="upload-video"),
   path('video/<int:movie_id>/' , VideoUploadView.as_view() , name="video-detail"),
]
