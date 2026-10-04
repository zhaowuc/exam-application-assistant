import random
from decimal import Decimal
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from . import models as m
from .serializers import PaperSerializer, model_serializer
from services import exams


@api_view(['POST'])
@transaction.atomic
def generate(request):
    try:
        count=int(request.data.get('count',20))
        duration=int(request.data.get('duration_minutes',30))
        if not 1<=count<=100 or not 1<=duration<=600: raise ValueError()
    except (TypeError,ValueError): raise ValidationError('题数应为1–100，时长应为1–600分钟。')
    exam_type=request.data.get('exam_type','civil')
    if exam_type not in ['civil','institution','graduate']: raise ValidationError('考试类型无效。')
    query=m.Question.objects.filter(is_active=True,exam_type=exam_type)
    for field in ['subject','difficulty','knowledge_point']:
        if request.data.get(field): query=query.filter(**{field:request.data[field]})
    ids=list(query.values_list('id',flat=True))
    if len(ids)<count: raise ValidationError(f'可用题目只有 {len(ids)} 道，请减少题数或放宽条件。')
    selected=list(m.Question.objects.filter(pk__in=random.sample(ids,count)))
    random.shuffle(selected)
    paper=m.ExamPaper.objects.create(title=request.data.get('title') or '我的专项模拟练习',exam_type=exam_type,
        subject=request.data.get('subject',''),total_questions=count,total_score=sum((q.points for q in selected),Decimal(0)),
        duration_minutes=duration,is_generated=True,created_by=request.user,blueprint=dict(request.data))
    m.PaperQuestion.objects.bulk_create([m.PaperQuestion(paper=paper,question=q,order=i+1,points=q.points) for i,q in enumerate(selected)])
    return Response(PaperSerializer(paper).data,status=201)


@api_view(['POST'])
def start(request):
    paper=get_object_or_404(m.ExamPaper,pk=request.data.get('paper'))
    if paper.created_by_id and paper.created_by_id!=request.user.id and not paper.is_demo:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('不能使用其他用户的私人试卷。')
    return Response(exams.represent(exams.start(request.user,paper)),status=201)


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=model_serializer(m.ExamAttempt)
    def get_queryset(self): return m.ExamAttempt.objects.filter(user=self.request.user).select_related('paper')
    def retrieve(self,request,*args,**kwargs): return Response(exams.represent(self.get_object()))
    @action(detail=True,methods=['post','patch'])
    def save(self,request,pk=None): return Response(exams.represent(exams.save(self.get_object(),request.data)))
    @action(detail=True,methods=['post'])
    def submit(self,request,pk=None):
        obj=self.get_object()
        if obj.status=='in_progress' and request.data.get('answers'): obj=exams.save(obj,request.data)
        return Response(exams.represent(exams.grade(obj)))


@api_view(['GET'])
def scores(request):
    query=m.ExamAttempt.objects.filter(user=request.user).exclude(status='in_progress').select_related('paper')
    return Response([{**model_serializer(m.ExamAttempt)(obj).data,'paper_title':obj.paper.title,'exam_type':obj.paper.exam_type} for obj in query[:300]])
