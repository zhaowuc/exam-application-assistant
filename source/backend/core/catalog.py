from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from . import models as m
from .serializers import model_serializer, OpportunitySerializer, SafeQuestionSerializer, PaperSerializer


class ReadOnly(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    def get_queryset(self):
        query = super().get_queryset()
        params = self.request.query_params
        for field in getattr(self,'filter_fields',[]):
            if params.get(field): query = query.filter(**{field:params[field]})
        if params.get('search'):
            conditions = Q()
            for field in getattr(self,'search_fields',[]): conditions |= Q(**{field+'__icontains':params['search']})
            if conditions: query = query.filter(conditions)
        return query


class OpportunityViewSet(ReadOnly):
    queryset = m.Opportunity.objects.filter(is_active=True).select_related('civil_detail','institution_detail','graduate_detail')
    serializer_class = OpportunitySerializer
    filter_fields = ['opportunity_type','year','region','education_required','source_type']
    search_fields = ['title','organization','code','major_requirement']
    @action(detail=True)
    def history(self,request,pk=None):
        return Response(model_serializer(m.HistoricalStat)(self.get_object().historical_stats.all(),many=True).data)
    @action(detail=True,permission_classes=[IsAuthenticated],methods=['get','post'])
    def matching(self,request,pk=None):
        from services.matching import match
        profile,_ = m.UserProfile.objects.get_or_create(user=request.user)
        return Response(match(self.get_object(),model_serializer(m.UserProfile)(profile).data))


class NoticeViewSet(ReadOnly):
    queryset=m.Notice.objects.filter(is_active=True)
    serializer_class=model_serializer(m.Notice)
    filter_fields=['exam_type','notice_type']
    search_fields=['title','content']


class ServiceViewSet(ReadOnly):
    queryset=m.ServiceResource.objects.filter(is_active=True)
    serializer_class=model_serializer(m.ServiceResource)
    filter_fields=['category','exam_type']
    search_fields=['title','content']


class QuestionViewSet(ReadOnly):
    permission_classes=[IsAuthenticated]
    queryset=m.Question.objects.filter(is_active=True).select_related('knowledge_point')
    serializer_class=SafeQuestionSerializer
    filter_fields=['exam_type','subject','question_type','category','knowledge_point','difficulty']
    search_fields=['stem']
    @action(detail=True,methods=['post'])
    def practice(self,request,pk=None):
        from services.exams import normalize
        question=self.get_object()
        answer=normalize(request.data.get('answer',[]))
        if not answer: 
            from rest_framework.exceptions import ValidationError
            raise ValidationError('请先选择答案。')
        return Response({'is_correct':answer==normalize(question.correct_answer),'correct_answer':question.correct_answer,'explanation':question.explanation})


class PaperViewSet(ReadOnly):
    permission_classes=[IsAuthenticated]
    queryset=m.ExamPaper.objects.all()
    serializer_class=PaperSerializer
    filter_fields=['exam_type','subject']
    search_fields=['title']
    def get_queryset(self):
        return super().get_queryset().filter(Q(created_by__isnull=True)|Q(created_by=self.request.user)|Q(is_demo=True))
    def get_serializer_context(self):
        return {**super().get_serializer_context(),'summary':self.action=='list'}


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    from django.db import connection
    with connection.cursor() as cursor: cursor.execute('SELECT 1')
    return Response({'status':'ok','version':'2.0.0','offline':True})


@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    return Response({'counts':{'opportunities':m.Opportunity.objects.filter(is_active=True).count(),'questions':m.Question.objects.filter(is_active=True).count(),'services':m.ServiceResource.objects.filter(is_active=True).count()},
        'notices':model_serializer(m.Notice)(m.Notice.objects.filter(is_active=True)[:4],many=True).data,
        'opportunities':OpportunitySerializer(m.Opportunity.objects.filter(is_active=True)[:6],many=True).data,
        'years':list(m.Opportunity.objects.order_by('-year').values_list('year',flat=True).distinct()),
        'regions':list(m.Opportunity.objects.order_by('region').values_list('region',flat=True).distinct()),
        'types':list(m.Opportunity.objects.values('opportunity_type').annotate(count=Count('id'))),
        'disclaimer':'本地演示数据不是实时招录公告；报考记录为本地管理，不代替官方报名。'})


def lookup(model,filters=()):
    @api_view(['GET'])
    def view(request):
        rows=model.objects.all()
        for field in filters:
            if request.query_params.get(field): rows=rows.filter(**{field:request.query_params[field]})
        return Response(model_serializer(model)(rows[:1000],many=True).data)
    return view
