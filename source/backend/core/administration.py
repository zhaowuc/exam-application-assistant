from django.db import transaction
from django.db.models import Q,Count,Avg
from django.conf import settings
from django.http import FileResponse
from pathlib import Path
from rest_framework import viewsets
from rest_framework.decorators import api_view,permission_classes,action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from . import models as m
from .security import IsAdmin
from .registry import RESOURCES,READONLY,serializer_for,metadata
from .serializers import model_serializer
from services import operations


class AdminViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdmin]
    resource=''
    def get_queryset(self):
        model=RESOURCES[self.resource][0]
        query=model.objects.all().order_by('-pk')
        params=self.request.query_params
        if self.resource=='applications':
            for key,target in [('exam_type','opportunity__opportunity_type'),('year','opportunity__year'),('region','opportunity__region')]:
                if params.get(key): query=query.filter(**{target:params[key]})
        if params.get('search'):
            condition=Q()
            for field in model._meta.fields:
                if field.get_internal_type() in ['CharField','TextField','EmailField']: condition |= Q(**{field.name+'__icontains':params['search']})
            if condition: query=query.filter(condition)
        for key in ['status','exam_type','opportunity_type','year','region','user','opportunity','category']:
            if params.get(key) and any(field.name==key for field in model._meta.fields): query=query.filter(**{key:params[key]})
        return query
    def get_serializer_class(self): return serializer_for(self.resource)
    def check_write(self):
        if self.resource in READONLY: raise ValidationError('此资源由系统生成，仅可查看与导出。')
    def check_exam_edit(self, obj=None):
        if self.resource=='questions' and obj and obj.answer_records.filter(attempt__status='in_progress').exists():
            raise ValidationError('题目正在考试中使用，请在考试结束后编辑。')
        paper_id=obj.paper_id if self.resource=='paper-questions' and obj else obj.pk if self.resource=='papers' and obj else self.request.data.get('paper') if self.resource=='paper-questions' else None
        if paper_id and m.ExamAttempt.objects.filter(paper_id=paper_id,status='in_progress').exists():
            raise ValidationError('试卷正在考试中使用，不能修改编排。')
    def sync_paper(self, obj):
        paper=obj.paper if self.resource=='paper-questions' else obj if self.resource=='papers' else None
        if paper:
            from django.db.models import Sum
            paper.total_questions=paper.paper_questions.count()
            paper.total_score=paper.paper_questions.aggregate(value=Sum('points'))['value'] or 0
            paper.save(update_fields=['total_questions','total_score'])
    @transaction.atomic
    def perform_create(self,serializer):
        self.check_write()
        self.check_exam_edit()
        if self.resource in ['applications','service-requests']: raise ValidationError('此资源由普通用户提交，管理员负责审核和回复。')
        obj=serializer.save()
        self.sync_paper(obj)
        operations.audit(self.request.user,'新增',self.resource,obj.pk)
    @transaction.atomic
    def perform_update(self,serializer):
        self.check_write()
        obj=serializer.instance
        self.check_exam_edit(obj)
        if self.resource=='users' and obj.role=='admin':
            if serializer.validated_data.get('role',obj.role)!='admin' or serializer.validated_data.get('status',obj.status)!='active':
                if obj.pk==self.request.user.pk or m.User.objects.filter(role='admin',status='active').count()<=1:
                    raise ValidationError('不能停用当前管理员或最后一个管理员。')
        if self.resource=='applications' and 'opportunity' in serializer.validated_data and serializer.validated_data['opportunity']!=obj.opportunity:
            raise ValidationError('不能改变报考记录关联的目标。')
        obj=serializer.save()
        self.sync_paper(obj)
        operations.audit(self.request.user,'编辑',self.resource,obj.pk)
        if self.resource in ['applications','service-requests']:
            m.Notification.objects.create(user=obj.user,title='报考记录更新' if self.resource=='applications' else '公共服务咨询更新',content=f'记录 #{obj.pk} 的处理状态：{obj.get_status_display()}。',link='/applications' if self.resource=='applications' else '/services')
    @transaction.atomic
    def perform_destroy(self,obj):
        self.check_write()
        self.check_exam_edit(obj)
        if self.resource=='users' and (obj.pk==self.request.user.pk or obj.role=='admin' and m.User.objects.filter(role='admin',status='active').count()<=1):
            raise ValidationError('不能删除当前或最后一个管理员。')
        pk=obj.pk
        paper=obj.paper if self.resource=='paper-questions' else None
        obj.delete()
        if paper:
            from django.db.models import Sum
            paper.total_questions=paper.paper_questions.count()
            paper.total_score=paper.paper_questions.aggregate(value=Sum('points'))['value'] or 0
            paper.save(update_fields=['total_questions','total_score'])
        operations.audit(self.request.user,'删除',self.resource,pk)
    @action(detail=False)
    def schema(self,request): return Response(metadata(self.resource))
    @action(detail=False)
    def export(self,request):
        query=self.get_queryset()
        if query.count()>10000: raise ValidationError('请筛选至10000条以内后导出。')
        operations.audit(request.user,'导出',self.resource)
        return operations.workbook_response(self.resource,self.get_serializer(query,many=True).data)
    @action(detail=False)
    def template(self,request): return operations.workbook_response(self.resource,[],True)
    @action(detail=False,methods=['post'],url_path='import')
    def import_data(self,request):
        return Response(model_serializer(m.ImportBatch)(operations.import_workbook(request.user,self.resource,request.FILES.get('file'))).data)


def admin_viewset(name):
    return type(name.replace('-','_').title()+'AdminViewSet',(AdminViewSet,),{'resource':name})


@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboard(request):
    return Response({'resources':[{'name':name,'label':label,'count':model.objects.count(),'readonly':name in READONLY} for name,(model,label,_) in RESOURCES.items()],
        'application_status':list(m.ApplicationRecord.objects.values('status').annotate(count=Count('id'))),
        'application_types':list(m.ApplicationRecord.objects.values('opportunity__opportunity_type').annotate(count=Count('id'))),
        'score_average':m.ExamAttempt.objects.exclude(status='in_progress').aggregate(value=Avg('score'))['value'],
        'database':Path(settings.DATABASES['default']['NAME']).name,'offline':True})


@api_view(['GET','POST'])
@permission_classes([IsAdmin])
def backups(request):
    if request.method=='POST': return Response({'filename':operations.backup(request.user)})
    folder=Path(settings.DATA_DIR)/'backups'
    return Response([{'filename':p.name,'size':p.stat().st_size} for p in sorted(folder.glob('backup_*.sqlite3'),reverse=True)] if folder.exists() else [])


@api_view(['GET'])
@permission_classes([IsAdmin])
def download_backup(request,filename):
    if Path(filename).name!=filename or not filename.startswith('backup_') or not filename.endswith('.sqlite3'): raise ValidationError('无效文件名。')
    path=(Path(settings.DATA_DIR)/'backups'/filename)
    if not path.is_file():
        from rest_framework.exceptions import NotFound
        raise NotFound('备份不存在。')
    return FileResponse(path.open('rb'),as_attachment=True,filename=filename)


@api_view(['POST'])
@permission_classes([IsAdmin])
def restore(request):
    if request.data.get('confirm')!='RESTORE': raise ValidationError('请确认恢复操作。')
    return Response(operations.restore(request.user,request.FILES.get('file')))
