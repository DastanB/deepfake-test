from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('orders', views.OrderReadOnlyViewSet, basename='orders')

urlpatterns = [
    path('upload/target_files', views.UploadTargetFilesView.as_view()),
    path('upload/source_files', views.UploadSourceFilesView.as_view()),
    path('orders/<int:pk>/source_files', views.UpdateSourceFilesView.as_view()),
    path('orders/<int:pk>/execute', views.ExecuteOrderView.as_view()),
    path('orders/<int:pk>/results', views.DownloadOrderResultsView.as_view()),
    path('source_files/<int:pk>/trim', views.TrimVideoFileView.as_view()),
    path('source_files/<int:pk>/preview/deepfaked', views.GetPreviewOfDeepfakedVideoFileView.as_view()),
    path('source_files/<int:pk>/preview', views.GetPreviewOfVideoFileView.as_view()),
] + router.urls
