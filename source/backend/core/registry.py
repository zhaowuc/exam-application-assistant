"""Single resource registry shared by admin CRUD, form metadata and import/export."""
from . import models as m
from .serializers import model_serializer, UserSerializer, OpportunitySerializer, ApplicationSerializer, ServiceRequestSerializer

RESOURCES = {
    'users': (m.User, '用户权限', UserSerializer),
    'opportunities': (m.Opportunity, '招考信息', OpportunitySerializer),
    'notices': (m.Notice, '公告资讯', None),
    'applications': (m.ApplicationRecord, '报考数据', ApplicationSerializer),
    'services': (m.ServiceResource, '公共服务资源', None),
    'service-requests': (m.ServiceRequest, '公共服务咨询', ServiceRequestSerializer),
    'majors': (m.Major, '专业目录', None),
    'major-categories': (m.MajorCategory, '专业分类', None),
    'requirement-rules': (m.RequirementRule, '资格匹配规则', None),
    'historical-stats': (m.HistoricalStat, '历史招考统计', None),
    'recommendation-rules': (m.RecommendationRule, '推荐权重', None),
    'question-categories': (m.QuestionCategory, '题目分类', None),
    'knowledge-points': (m.KnowledgePoint, '知识点', None),
    'questions': (m.Question, '题库管理', None),
    'papers': (m.ExamPaper, '试卷管理', None),
    'paper-questions': (m.PaperQuestion, '试卷题目编排', None),
    'attempts': (m.ExamAttempt, '考试成绩', None),
    'notifications': (m.Notification, '消息通知', None),
    'settings': (m.SystemConfig, '系统设置', None),
    'import-batches': (m.ImportBatch, '导入日志', None),
    'audit-logs': (m.AuditLog, '操作审计', None),
}
READONLY = {'attempts', 'import-batches', 'audit-logs'}


def serializer_for(name):
    model, label, custom = RESOURCES[name]
    return custom or model_serializer(model)


def display(obj):
    for field in ['username', 'title', 'name', 'stem', 'candidate_name', 'subject', 'key', 'file_name', 'action']:
        if hasattr(obj, field) and getattr(obj, field):
            return str(getattr(obj, field))[:100]
    return f'#{obj.pk}'


def metadata(name):
    from rest_framework import serializers
    fields = []
    for key, field in serializer_for(name)().fields.items():
        if field.read_only or key == 'id':
            continue
        typ = 'text'
        if isinstance(field, serializers.BooleanField): typ = 'boolean'
        elif isinstance(field, serializers.ChoiceField): typ = 'choice'
        elif isinstance(field, serializers.PrimaryKeyRelatedField): typ = 'relation'
        elif isinstance(field, serializers.JSONField): typ = 'json'
        elif isinstance(field, serializers.IntegerField): typ = 'integer'
        elif isinstance(field, (serializers.DecimalField, serializers.FloatField)): typ = 'number'
        elif isinstance(field, serializers.DateTimeField): typ = 'datetime'
        elif isinstance(field, serializers.DateField): typ = 'date'
        elif key in ['content', 'description', 'stem', 'explanation', 'notes', 'review_notes', 'response', 'other_conditions', 'major_requirement']: typ = 'textarea'
        elif key == 'password': typ = 'password'
        spec = {'key':key, 'label':str(field.label or key), 'type':typ, 'required':field.required,
            'nullable':field.allow_null, 'max_length':getattr(field,'max_length',None)}
        if typ == 'choice': spec['choices'] = [{'value':v,'label':str(label)} for v,label in field.choices.items()]
        if typ == 'relation':
            cls = field.queryset.model
            spec['resource'] = next((n for n, (model, _, _) in RESOURCES.items() if model == cls), '')
            spec['options'] = [{'value':obj.pk,'label':display(obj)} for obj in cls.objects.all()[:1000]]
        fields.append(spec)
    return {'name':name,'label':RESOURCES[name][1], 'readonly':name in READONLY, 'fields':fields}
