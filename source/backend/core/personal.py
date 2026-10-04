from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from . import models as m
from .serializers import model_serializer, OpportunitySerializer, ApplicationSerializer, ServiceRequestSerializer


class OwnedViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    @transaction.atomic
    def perform_update(self,serializer): serializer.save()


class PlanViewSet(OwnedViewSet):
    queryset=m.ApplicationPlan.objects.all()
    serializer_class=model_serializer(m.ApplicationPlan,read_only=('user',))
    def perform_create(self,serializer):
        values=serializer.validated_data
        if values.get('registration_start') and values.get('registration_end') and values['registration_start']>values['registration_end']:
            raise ValidationError('报名结束日期不能早于开始日期。')
        super().perform_create(serializer)


class ExamProfileViewSet(OwnedViewSet):
    queryset=m.ExamProfile.objects.all()
    serializer_class=model_serializer(m.ExamProfile,read_only=('user',))


class FavoriteSerializer(model_serializer(m.Favorite,read_only=('user',))):
    def to_representation(self,obj):
        return {**super().to_representation(obj),'opportunity_detail':OpportunitySerializer(obj.opportunity).data}


class FavoriteViewSet(OwnedViewSet):
    queryset=m.Favorite.objects.select_related('opportunity').all()
    serializer_class=FavoriteSerializer


class ComparisonViewSet(OwnedViewSet):
    queryset=m.ComparisonRecord.objects.all()
    serializer_class=model_serializer(m.ComparisonRecord,read_only=('user','snapshot'))
    def perform_create(self,serializer):
        opportunities=serializer.validated_data.get('opportunities',[])
        if not 2<=len(opportunities)<=4: raise ValidationError('请选择 2–4 个目标进行比较。')
        serializer.save(user=self.request.user,snapshot={'opportunities':OpportunitySerializer(opportunities,many=True).data})
    def perform_update(self,serializer):
        opportunities=serializer.validated_data.get('opportunities',list(serializer.instance.opportunities.all()))
        if not 2<=len(opportunities)<=4: raise ValidationError('请选择 2–4 个目标进行比较。')
        serializer.save(snapshot={'opportunities':OpportunitySerializer(opportunities,many=True).data})


class ApplicationViewSet(OwnedViewSet):
    queryset=m.ApplicationRecord.objects.select_related('user','opportunity').all()
    serializer_class=ApplicationSerializer
    def validate_user_data(self,serializer):
        values=serializer.validated_data
        if any(key in values for key in ['review_notes','score','result']): raise ValidationError('审核与成绩字段仅管理员可修改。')
        if values.get('status','submitted') not in ['draft','submitted','cancelled']: raise ValidationError('不能自行设置审核状态。')
        if 'materials' in values and (not isinstance(values['materials'],list) or any(not isinstance(v,str) for v in values['materials'])):
            raise ValidationError('材料清单应为字符串数组。')
        opportunity=values.get('opportunity')
        if opportunity and not opportunity.is_active: raise ValidationError('此目标已经停用。')
    def perform_create(self,serializer):
        self.validate_user_data(serializer)
        super().perform_create(serializer)
    def perform_update(self,serializer):
        self.validate_user_data(serializer)
        obj=serializer.instance
        if 'opportunity' in serializer.validated_data and serializer.validated_data['opportunity']!=obj.opportunity:
            raise ValidationError('不能更换已有记录的报考目标。')
        if obj.status not in ['draft','submitted','rejected'] and serializer.validated_data!={'status':'cancelled'}:
            raise ValidationError('记录已进入审核或完成阶段，仅可取消。')
        serializer.save()
    def perform_destroy(self,obj):
        if obj.status not in ['draft','cancelled']: raise ValidationError('仅草稿和已取消记录可以删除。')
        obj.delete()


class ServiceRequestViewSet(OwnedViewSet):
    queryset=m.ServiceRequest.objects.all()
    serializer_class=ServiceRequestSerializer
    def perform_create(self,serializer):
        if any(key in serializer.validated_data for key in ['status','response']): raise ValidationError('回复和处理状态由管理员设置。')
        super().perform_create(serializer)
    def perform_update(self,serializer):
        if any(key in serializer.validated_data for key in ['status','response']): raise ValidationError('回复和处理状态由管理员设置。')
        if serializer.instance.status!='pending': raise ValidationError('已回复的咨询不能修改。')
        serializer.save()
    def perform_destroy(self,obj):
        if obj.status!='pending': raise ValidationError('已回复的咨询不能删除。')
        obj.delete()


class WrongSerializer(model_serializer(m.WrongQuestion,read_only=('user','question','attempt_count','wrong_count','correct_count','last_answered_at','average_time_seconds'))):
    def to_representation(self,obj):
        return {**super().to_representation(obj),'question_detail':model_serializer(m.Question)(obj.question).data}


class WrongViewSet(OwnedViewSet):
    queryset=m.WrongQuestion.objects.select_related('question').all()
    serializer_class=WrongSerializer
    http_method_names=['get','patch','delete','head','options']


@api_view(['GET','POST'])
def recommendations(request):
    from services.matching import recommend
    obj,_=m.UserProfile.objects.get_or_create(user=request.user)
    profile=model_serializer(m.UserProfile)(obj).data
    query=m.Opportunity.objects.filter(is_active=True).prefetch_related('requirement_rules')
    if request.query_params.get('opportunity_type'): query=query.filter(opportunity_type=request.query_params['opportunity_type'])
    result=[]
    for opportunity in query[:1000]:
        row=recommend(opportunity,profile)
        if row: result.append({**row,'opportunity':OpportunitySerializer(opportunity).data})
    result.sort(key=lambda row:row['score'],reverse=True)
    if request.method=='POST':
        with transaction.atomic():
            for row in result[:30]:
                m.RecommendationRecord.objects.create(user=request.user,opportunity_id=row['opportunity']['id'],**{key:value for key,value in row.items() if key!='opportunity'})
    return Response({'count':len(result),'results':result[:30],'limited_to':1000})


@api_view(['GET'])
def recommendation_history(request):
    return Response(model_serializer(m.RecommendationRecord)(m.RecommendationRecord.objects.filter(user=request.user)[:100],many=True).data)


@api_view(['GET','POST'])
def weakness(request):
    if request.method=='POST':
        from services.exams import rebuild_weakness
        rebuild_weakness(request.user)
    data=[]
    for obj in m.WeaknessAnalysis.objects.filter(user=request.user).select_related('knowledge_point'):
        data.append({**model_serializer(m.WeaknessAnalysis)(obj).data,'knowledge_name':obj.knowledge_point.name if obj.knowledge_point else '综合'})
    return Response(data)


def notifications_for(user):
    now=timezone.now()
    today=timezone.localdate()
    from datetime import timedelta
    plans=m.ApplicationPlan.objects.filter(user=user,remind=True).exclude(status__in=['completed','cancelled','expired'])
    for plan in plans:
        for field,label in [('registration_end','报名截止'),('exam_date','考试日期')]:
            when=getattr(plan,field)
            if when and today<=when<=today+timedelta(days=7):
                m.Notification.objects.get_or_create(user=user,title=f'{plan.title or plan.target_name} · {label}提醒',
                    link='/applications',content=f'计划 #{plan.pk} 的{label}为 {when}。请提前核对官方时间并完成准备。',defaults={'notification_type':'exam' if field=='exam_date' else 'registration_deadline'})
    enabled=list(m.ExamProfile.objects.filter(user=user,enabled=True).values_list('exam_type',flat=True))
    return m.Notification.objects.filter(is_active=True).filter(Q(user=user)|Q(user__isnull=True,target__in=['all']+enabled)).filter(Q(scheduled_at__isnull=True)|Q(scheduled_at__lte=now))


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=model_serializer(m.Notification)
    def get_queryset(self): return notifications_for(self.request.user)
    def list(self,request,*args,**kwargs):
        response=super().list(request,*args,**kwargs)
        read=set(m.NotificationReceipt.objects.filter(user=request.user,is_read=True).values_list('notification_id',flat=True))
        for row in response.data['results']: row['is_read']=row['id'] in read
        return response
    @action(detail=True,methods=['post'])
    def read(self,request,pk=None):
        m.NotificationReceipt.objects.update_or_create(user=request.user,notification=self.get_object(),defaults={'is_read':True,'read_at':timezone.now()})
        return Response({'is_read':True})
    @action(detail=False,methods=['post'],url_path='read-all')
    def read_all(self,request):
        for obj in self.get_queryset(): m.NotificationReceipt.objects.update_or_create(user=request.user,notification=obj,defaults={'is_read':True,'read_at':timezone.now()})
        return Response({'is_read':True})
