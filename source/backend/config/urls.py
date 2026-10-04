from django.urls import path,include,re_path
from django.http import FileResponse,JsonResponse,Http404
from django.conf import settings
from pathlib import Path
from rest_framework.routers import DefaultRouter
from core import accounts,catalog,personal,exam_views,administration,models as m
from core.registry import RESOURCES

router=DefaultRouter()
for name,view in {'opportunities':catalog.OpportunityViewSet,'notices':catalog.NoticeViewSet,'services':catalog.ServiceViewSet,
    'questions':catalog.QuestionViewSet,'papers':catalog.PaperViewSet,'favorites':personal.FavoriteViewSet,
    'comparisons':personal.ComparisonViewSet,'application-plans':personal.PlanViewSet,'applications':personal.ApplicationViewSet,
    'service-requests':personal.ServiceRequestViewSet,'exam-profiles':personal.ExamProfileViewSet,
    'wrong-questions':personal.WrongViewSet,'notifications':personal.NotificationViewSet,'attempts':exam_views.AttemptViewSet}.items():
    router.register(name,view,basename=name)
for name in RESOURCES: router.register('admin/'+name,administration.admin_viewset(name),basename='admin-'+name)


def frontend(request,asset=''):
    folder=Path(settings.RESOURCE_DIR)/'frontend_dist'
    target=(folder/asset).resolve()
    if not target.is_relative_to(folder.resolve()): raise Http404()
    if target.is_file():
        response=FileResponse(target.open('rb'))
        response['Cache-Control']='public, max-age=31536000, immutable' if asset.startswith('assets/') else 'no-cache'
        response['X-Content-Type-Options']='nosniff'
        return response
    if asset.startswith(('assets/','api/')): raise Http404()
    target=folder/'index.html'
    if target.is_file():
        response=FileResponse(target.open('rb'),content_type='text/html; charset=utf-8')
        response['Cache-Control']='no-store'
        response['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
        return response
    return JsonResponse({'message':'前端尚未构建，请运行前端构建命令。'},status=503)


urlpatterns=[
    path('api/v1/health/',catalog.health),path('api/v1/home/',catalog.home),
    path('api/v1/auth/login/',accounts.login),path('api/v1/auth/register/',accounts.register),path('api/v1/auth/refresh/',accounts.refresh),
    path('api/v1/auth/me/',accounts.me),path('api/v1/auth/logout/',accounts.logout),path('api/v1/auth/change-password/',accounts.change_password),
    path('api/v1/profile/',accounts.profile),path('api/v1/recommendations/',personal.recommendations),path('api/v1/recommendations/history/',personal.recommendation_history),
    path('api/v1/weakness/',personal.weakness),path('api/v1/papers/generate/',exam_views.generate),path('api/v1/exams/start/',exam_views.start),
    path('api/v1/scores/',exam_views.scores),path('api/v1/majors/',catalog.lookup(m.Major)),path('api/v1/major-categories/',catalog.lookup(m.MajorCategory)),
    path('api/v1/question-categories/',catalog.lookup(m.QuestionCategory,('exam_type','subject'))),path('api/v1/knowledge-points/',catalog.lookup(m.KnowledgePoint,('category',))),
    path('api/v1/admin/dashboard/',administration.dashboard),path('api/v1/admin/backups/',administration.backups),
    path('api/v1/admin/backups/<str:filename>/',administration.download_backup),path('api/v1/admin/restore/',administration.restore),
    path('api/v1/',include(router.urls)),re_path(r'^(?P<asset>.*)$',frontend),
]
