from rest_framework import serializers
from . import models as m
from .extensions import ServiceResource, ServiceRequest, ApplicationRecord


class ValidatedModelSerializer(serializers.ModelSerializer):
    def validate(self, data):
        model = self.Meta.model
        if self.instance and model == m.Question and self.instance.answer_records.filter(attempt__status='in_progress').exists():
            raise serializers.ValidationError('题目正在考试中使用，暂不能编辑或批量更新。')
        paper = data.get('paper',getattr(self.instance,'paper',None)) if model == m.PaperQuestion else self.instance if model == m.ExamPaper else None
        if paper and paper.attempts.filter(status='in_progress').exists():
            raise serializers.ValidationError('试卷正在考试中使用，暂不能修改编排。')
        for field in self.Meta.model._meta.fields:
            if field.name not in data:
                continue
            value = data[field.name]
            if isinstance(field, __import__('django').db.models.JSONField) and value is not None:
                default = field.get_default()
                if isinstance(default, (list, dict)) and not isinstance(value, type(default)):
                    raise serializers.ValidationError({field.name:'JSON类型不正确，应为'+('数组' if isinstance(default,list) else '对象')})
            if field.name in ['score','points','total_score'] and value is not None and value < 0:
                raise serializers.ValidationError({field.name:'不能小于零。'})
        if self.Meta.model == m.Question:
            options = data.get('options', getattr(self.instance,'options',[]))
            answer = data.get('correct_answer', getattr(self.instance,'correct_answer',[]))
            kind = data.get('question_type', getattr(self.instance,'question_type','single'))
            if not options or any(not isinstance(o,dict) or not isinstance(o.get('key'),str) or not isinstance(o.get('text'),str) for o in options):
                raise serializers.ValidationError({'options':'需为带 key 与 text 的选项对象数组。'})
            keys = [o['key'] for o in options]
            if len(set(keys)) != len(keys) or not answer or any(a not in keys for a in answer):
                raise serializers.ValidationError({'correct_answer':'答案必须对应唯一的有效选项标识。'})
            if kind != 'multiple' and len(answer) != 1:
                raise serializers.ValidationError({'correct_answer':'单选和判断题必须只有一个正确答案。'})
        return data


def model_serializer(model, exclude=(), read_only=()):
    meta = type('Meta', (), {'model': model, 'exclude': tuple(exclude), 'read_only_fields': tuple(read_only) + ('created_at', 'updated_at', 'is_demo')})
    return type(model.__name__ + 'Serializer', (ValidatedModelSerializer,), {'Meta': meta})


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = m.User
        fields = ['id', 'username', 'email', 'phone', 'role', 'status', 'is_demo', 'date_joined', 'password']
        read_only_fields = ['is_demo', 'date_joined']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': '请设置密码。'})
        return m.User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        if password or any(key in validated_data and validated_data[key] != getattr(instance, key) for key in ('role', 'status')):
            instance.auth_version += 1
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class OpportunitySerializer(serializers.ModelSerializer):
    competition_ratio = serializers.FloatField(read_only=True)
    detail = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = m.Opportunity
        fields = '__all__'
        read_only_fields = ['view_count', 'created_at', 'updated_at']

    def to_representation(self, instance):
        result = super().to_representation(instance)
        for key in ('civil_detail', 'institution_detail', 'graduate_detail'):
            try:
                obj = getattr(instance, key)
                result[key] = model_serializer(type(obj))(obj).data
            except (AttributeError, m.Opportunity.DoesNotExist):
                pass
        return result

    def validate(self, data):
        if data.get('slots',getattr(self.instance,'slots',1)) < 1:
            raise serializers.ValidationError({'slots':'招录名额至少为1。'})
        for key in ['certificates_required']:
            if key in data and not isinstance(data[key],list):
                raise serializers.ValidationError({key:'应为数组。'})
        minimum=data.get('min_age',getattr(self.instance,'min_age',None))
        maximum=data.get('max_age',getattr(self.instance,'max_age',35))
        if minimum is not None and minimum>maximum:
            raise serializers.ValidationError('最小年龄不能大于最大年龄。')
        if 'detail' in data and not isinstance(data['detail'],dict):
            raise serializers.ValidationError({'detail':'应为JSON对象。'})
        return data

    def create(self, data):
        detail = data.pop('detail', {})
        obj = super().create(data)
        self.save_detail(obj, detail)
        return obj

    def update(self, obj, data):
        detail = data.pop('detail', None)
        if 'opportunity_type' in data and data['opportunity_type'] != obj.opportunity_type:
            raise serializers.ValidationError('已有记录不能改变考试类型，请新增另一记录。')
        obj = super().update(obj, data)
        if detail is not None:
            self.save_detail(obj, detail)
        return obj

    def save_detail(self, obj, detail):
        cls = {'civil': m.CivilServicePosition, 'institution': m.InstitutionPosition, 'graduate': m.GraduateProgram}[obj.opportunity_type]
        previous = cls.objects.filter(opportunity=obj).first()
        serializer = model_serializer(cls)(previous, data={**detail, 'opportunity': obj.id}, partial=previous is not None)
        serializer.is_valid(raise_exception=True)
        serializer.save()


class SafeQuestionSerializer(serializers.ModelSerializer):
    knowledge_name = serializers.CharField(source='knowledge_point.name', read_only=True)

    class Meta:
        model = m.Question
        exclude = ['correct_answer', 'explanation']


class PaperSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = m.ExamPaper
        fields = '__all__'

    def get_questions(self, obj):
        request = self.context.get('request')
        if request and self.context.get('summary'):
            return []
        return [{**SafeQuestionSerializer(item.question).data, 'order': item.order, 'paper_points': str(item.points)} for item in obj.paper_questions.select_related('question__knowledge_point').all()]


class ApplicationSerializer(ValidatedModelSerializer):
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    organization = serializers.CharField(source='opportunity.organization', read_only=True)
    exam_type = serializers.CharField(source='opportunity.opportunity_type', read_only=True)
    year = serializers.IntegerField(source='opportunity.year', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ApplicationRecord
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class ServiceRequestSerializer(ValidatedModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
