"""Recovered ORM declarations; editable Python source. Schema matches original delivery data."""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import django.contrib.auth.validators
from decimal import Decimal
import uuid

class User(AbstractUser):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    password = models.CharField(verbose_name='密码', max_length=128)
    last_login = models.DateTimeField(verbose_name='上次登录', blank=True, null=True)
    is_superuser = models.BooleanField(verbose_name='超级用户状态', default=False, help_text='指明该用户缺省拥有所有权限。')
    username = models.CharField(verbose_name='用户名', max_length=150, unique=True, help_text='必填；长度为150个字符或以下；只能包含字母、数字、特殊字符“@”、“.”、“-”和“_”。', validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], error_messages={'unique': '已存在一位使用该名字的用户。'})
    first_name = models.CharField(verbose_name='名字', max_length=150, blank=True)
    last_name = models.CharField(verbose_name='姓氏', max_length=150, blank=True)
    is_staff = models.BooleanField(verbose_name='工作人员状态', default=False, help_text='指明用户是否可以登录到这个管理站点。')
    is_active = models.BooleanField(verbose_name='有效', default=True, help_text='指明用户是否被认为是活跃的。以反选代替删除帐号。')
    date_joined = models.DateTimeField(verbose_name='加入日期', default=timezone.now)
    email = models.EmailField(max_length=254, blank=True)
    role = models.CharField(max_length=16, db_index=True, default='user', choices=[('user', '普通用户'), ('admin', '管理员')])
    status = models.CharField(max_length=16, db_index=True, default='active', choices=[('active', '正常'), ('disabled', '停用')])
    phone = models.CharField(max_length=32, blank=True)
    is_demo = models.BooleanField(db_index=True, default=False)
    auth_version = models.PositiveIntegerField(default=1)
    groups = models.ManyToManyField(verbose_name='组', blank=True, help_text='该用户归属的组。一个用户将得到其归属的组的所有权限。', related_name='user_set', related_query_name='user', to='auth.group')
    user_permissions = models.ManyToManyField(verbose_name='用户权限', blank=True, help_text='这个用户的特定权限。', related_name='user_set', related_query_name='user', to='auth.permission')

    class Meta:
        db_table = 'core_user'

    def save(self, *args, **kwargs):
        self.is_staff = self.role == 'admin'
        self.is_active = self.status == 'active'
        if kwargs.get('update_fields'):
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'is_staff', 'is_active'}
        super().save(*args, **kwargs)


class MajorCategory(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, blank=True)
    level = models.CharField(max_length=20, default='category', choices=[('discipline', '学科门类'), ('category', '专业大类')])
    parent = models.ForeignKey(blank=True, null=True, related_name='children', on_delete=models.CASCADE, to='core.majorcategory')
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_majorcategory'
        ordering = ['code', 'name']
        constraints = [models.UniqueConstraint(name='unique_major_category_parent', fields=('name', 'parent'))]


class Major(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(related_name='majors', on_delete=models.PROTECT, to='core.majorcategory')
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=32, blank=True)
    aliases = models.JSONField(blank=True, default=list)
    related_names = models.JSONField(blank=True, default=list)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_major'
        ordering = ['code', 'name']


class UserProfile(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(related_name='profile', on_delete=models.CASCADE, to='core.user')
    nickname = models.CharField(max_length=64, blank=True)
    real_name = models.CharField(max_length=64, blank=True)
    birth_year = models.PositiveSmallIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=16, blank=True)
    region = models.CharField(max_length=64, blank=True)
    education = models.CharField(max_length=20, blank=True, choices=[('high_school', '高中及以下'), ('college', '大专'), ('bachelor', '本科'), ('master', '硕士'), ('doctor', '博士')])
    degree = models.CharField(max_length=40, blank=True)
    major = models.ForeignKey(blank=True, null=True, related_name='profiles', on_delete=models.SET_NULL, to='core.major')
    major_text = models.CharField(max_length=100, blank=True)
    graduation_status = models.CharField(max_length=40, blank=True)
    is_fresh_graduate = models.BooleanField(blank=True, null=True)
    political_status = models.CharField(max_length=40, blank=True)
    household_region = models.CharField(max_length=64, blank=True)
    origin_region = models.CharField(max_length=64, blank=True)
    grassroots_years = models.PositiveSmallIntegerField(default=0)
    work_years = models.PositiveSmallIntegerField(default=0)
    work_experience = models.TextField(blank=True)
    certificates = models.JSONField(blank=True, default=list)
    target_regions = models.JSONField(blank=True, default=list)
    target_unit_types = models.JSONField(blank=True, default=list)
    school_preferences = models.JSONField(blank=True, default=list)
    preferences = models.JSONField(blank=True, default=dict)
    mock_scores = models.JSONField(blank=True, default=dict)

    class Meta:
        db_table = 'core_userprofile'

    @property
    def age(self):
        return timezone.localdate().year - self.birth_year if self.birth_year else None


class ExamProfile(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='exam_profiles', on_delete=models.CASCADE, to='core.user')
    exam_type = models.CharField(max_length=20, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    target_year = models.PositiveSmallIntegerField(blank=True, null=True)
    target_regions = models.JSONField(blank=True, default=list)
    target_subjects = models.JSONField(blank=True, default=list)
    preferences = models.JSONField(blank=True, default=dict)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_examprofile'
        constraints = [models.UniqueConstraint(name='unique_user_exam_profile', fields=('user', 'exam_type'))]


class Notice(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    exam_type = models.CharField(max_length=20, db_index=True, default='all', choices=[('all', '全部'), ('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    notice_type = models.CharField(max_length=20, default='announcement', choices=[('announcement', '公告'), ('guide', '简章'), ('reminder', '提醒'), ('system', '系统')])
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    content = models.TextField()
    publisher = models.CharField(max_length=100, blank=True)
    published_at = models.DateTimeField(db_index=True, default=timezone.now)
    deadline = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=255, default='本地演示数据')
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(db_index=True, default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_notice'
        ordering = ['-published_at', '-id']


class Opportunity(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    opportunity_type = models.CharField(max_length=20, db_index=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    year = models.PositiveSmallIntegerField(db_index=True)
    region = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=100, db_index=True)
    organization = models.CharField(max_length=255, blank=True, db_index=True)
    department = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    slots = models.PositiveIntegerField(default=1)
    education_required = models.CharField(max_length=40, default='不限')
    degree_required = models.CharField(max_length=40, default='不限')
    major_requirement = models.TextField(default='不限')
    political_status = models.CharField(max_length=50, default='不限')
    fresh_graduate_requirement = models.CharField(max_length=20, default='unrestricted', choices=[('unrestricted', '不限'), ('required', '要求应届'), ('not_required', '要求非应届')])
    grassroots_years = models.PositiveSmallIntegerField(default=0)
    work_years = models.PositiveSmallIntegerField(default=0)
    household_requirement = models.CharField(max_length=100, default='不限')
    min_age = models.PositiveSmallIntegerField(blank=True, null=True)
    max_age = models.PositiveSmallIntegerField(default=35)
    certificates_required = models.JSONField(blank=True, default=list)
    other_conditions = models.TextField(blank=True)
    application_count = models.PositiveIntegerField(default=0)
    approved_count = models.PositiveIntegerField(default=0)
    lowest_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    average_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    highest_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    source = models.CharField(max_length=255, default='本地演示数据')
    source_type = models.CharField(max_length=32, default='demo', choices=[('official_public', '官方公开'), ('authorized', '授权数据'), ('demo', '演示数据'), ('imported', '用户导入')])
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(db_index=True, default=True)
    published_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        db_table = 'core_opportunity'
        ordering = ['-year', '-published_at', 'id']
        constraints = [models.UniqueConstraint(name='unique_opportunity_code_year', fields=('opportunity_type', 'year', 'code'))]
        indexes = [models.Index(name='core_opport_opportu_8a5948_idx', fields=['opportunity_type', 'year', 'region']), models.Index(name='core_opport_opportu_6fcbbf_idx', fields=['opportunity_type', 'is_active'])]

    @property
    def competition_ratio(self):
        return round(self.approved_count / self.slots, 2) if self.slots else 0


class CivilServicePosition(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    opportunity = models.OneToOneField(related_name='civil_detail', on_delete=models.CASCADE, to='core.opportunity')
    exam_type = models.CharField(max_length=100, default='省级公务员考试')
    recruiting_agency = models.CharField(max_length=255)
    employing_unit = models.CharField(max_length=255)
    job_introduction = models.TextField(blank=True)

    class Meta:
        db_table = 'core_civilserviceposition'


class InstitutionPosition(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    opportunity = models.OneToOneField(related_name='institution_detail', on_delete=models.CASCADE, to='core.opportunity')
    institution_name = models.CharField(max_length=255)
    position_category = models.CharField(max_length=100, blank=True)
    specialty = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'core_institutionposition'


class GraduateProgram(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    opportunity = models.OneToOneField(related_name='graduate_detail', on_delete=models.CASCADE, to='core.opportunity')
    university_name = models.CharField(max_length=255)
    university_code = models.CharField(max_length=50)
    university_tier = models.CharField(max_length=100, blank=True)
    college_name = models.CharField(max_length=255)
    program_name = models.CharField(max_length=255)
    program_code = models.CharField(max_length=50)
    research_direction = models.CharField(max_length=255, blank=True)
    degree_type = models.CharField(max_length=30, default='专业硕士')
    study_mode = models.CharField(max_length=30, default='全日制')
    recommended_exempt = models.PositiveIntegerField(default=0)
    unified_slots = models.PositiveIntegerField(default=0)
    exam_subjects = models.JSONField(blank=True, default=list)
    cross_major_requirement = models.CharField(max_length=255, default='允许跨考')
    bachelor_major_requirement = models.TextField(default='不限')
    national_line = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    university_line = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    retest_line = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    minimum_admission_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    average_admission_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    admitted_count = models.PositiveIntegerField(default=0)
    admission_ratio = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'core_graduateprogram'


class RequirementRule(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    opportunity = models.ForeignKey(related_name='requirement_rules', on_delete=models.CASCADE, to='core.opportunity')
    field_name = models.CharField(max_length=64)
    label = models.CharField(max_length=100)
    operator = models.CharField(max_length=20, default='eq', choices=[('eq', '等于'), ('in', '属于'), ('gte', '大于等于'), ('lte', '小于等于'), ('contains', '包含'), ('major', '专业匹配'), ('manual', '人工确认')])
    expected_value = models.JSONField(default=dict)
    is_hard = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'core_requirementrule'
        ordering = ['sort_order', 'id']


class HistoricalStat(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    opportunity = models.ForeignKey(related_name='historical_stats', on_delete=models.CASCADE, to='core.opportunity')
    year = models.PositiveSmallIntegerField(db_index=True)
    slots = models.PositiveIntegerField(default=0)
    applicants = models.PositiveIntegerField(default=0)
    approved = models.PositiveIntegerField(default=0)
    admitted = models.PositiveIntegerField(default=0)
    minimum_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    average_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    maximum_score = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    extra_data = models.JSONField(blank=True, default=dict)

    class Meta:
        db_table = 'core_historicalstat'
        ordering = ['year']
        constraints = [models.UniqueConstraint(name='unique_opportunity_history_year', fields=('opportunity', 'year'))]

    @property
    def competition_ratio(self):
        return round(self.approved / self.slots, 2) if self.slots else 0


class Favorite(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='favorites', on_delete=models.CASCADE, to='core.user')
    opportunity = models.ForeignKey(related_name='favorited_by', on_delete=models.CASCADE, to='core.opportunity')
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'core_favorite'
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(name='unique_user_favorite', fields=('user', 'opportunity'))]


class ComparisonRecord(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='comparisons', on_delete=models.CASCADE, to='core.user')
    title = models.CharField(max_length=255, blank=True)
    snapshot = models.JSONField(blank=True, default=dict)
    opportunities = models.ManyToManyField(related_name='comparison_records', to='core.opportunity')

    class Meta:
        db_table = 'core_comparisonrecord'
        ordering = ['-created_at']


class RecommendationRecord(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='recommendations', on_delete=models.CASCADE, to='core.user')
    opportunity = models.ForeignKey(related_name='recommendations', on_delete=models.CASCADE, to='core.opportunity')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    level = models.CharField(max_length=20, choices=[('sprint', '冲刺'), ('steady', '稳妥'), ('safe', '保守'), ('not_recommended', '不推荐')])
    qualification_status = models.CharField(max_length=30)
    breakdown = models.JSONField(default=dict)
    explanation = models.TextField()
    strengths = models.JSONField(default=list)
    risks = models.JSONField(default=list)
    advice = models.TextField(blank=True)

    class Meta:
        db_table = 'core_recommendationrecord'
        ordering = ['-score', '-created_at']


class RecommendationRule(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, db_index=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    key = models.CharField(max_length=40)
    weight = models.DecimalField(validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('100'))], max_digits=6, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(db_index=True, default=True)

    class Meta:
        db_table = 'core_recommendationrule'
        ordering = ['exam_type', 'id']
        constraints = [models.UniqueConstraint(name='unique_recommendation_weight', fields=('exam_type', 'key'))]


class ApplicationPlan(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='application_plans', on_delete=models.CASCADE, to='core.user')
    opportunity = models.ForeignKey(blank=True, null=True, related_name='application_plans', on_delete=models.CASCADE, to='core.opportunity')
    title = models.CharField(max_length=255, blank=True)
    exam_type = models.CharField(max_length=20, blank=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    target_name = models.CharField(max_length=255, blank=True)
    registration_start = models.DateField(blank=True, null=True)
    registration_end = models.DateField(blank=True, null=True)
    exam_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='preparing', choices=[('preparing', '准备中'), ('registered', '已报名'), ('planned', '计划中'), ('applied', '已报名'), ('paid', '已缴费'), ('completed', '已完成'), ('expired', '已过期'), ('cancelled', '已取消')])
    deadline = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    reminders = models.JSONField(blank=True, default=list)
    remind = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_applicationplan'
        ordering = ['-created_at']


class QuestionCategory(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    exam_type = models.CharField(max_length=20, db_index=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    subject = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(blank=True, null=True, related_name='children', on_delete=models.CASCADE, to='core.questioncategory')

    class Meta:
        db_table = 'core_questioncategory'
        constraints = [models.UniqueConstraint(name='unique_question_category', fields=('exam_type', 'subject', 'name', 'parent'))]


class KnowledgePoint(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(related_name='knowledge_points', on_delete=models.CASCADE, to='core.questioncategory')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(blank=True, null=True, related_name='children', on_delete=models.CASCADE, to='core.knowledgepoint')
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_knowledgepoint'
        constraints = [models.UniqueConstraint(name='unique_knowledge_point', fields=('category', 'name', 'parent'))]


class Question(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    exam_type = models.CharField(max_length=20, db_index=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    subject = models.CharField(max_length=100, db_index=True)
    question_type = models.CharField(max_length=20, db_index=True, choices=[('single', '单选题'), ('multiple', '多选题'), ('true_false', '判断题')])
    category = models.ForeignKey(related_name='questions', on_delete=models.PROTECT, to='core.questioncategory')
    knowledge_point = models.ForeignKey(related_name='questions', on_delete=models.PROTECT, to='core.knowledgepoint')
    year = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True)
    stem = models.TextField()
    options = models.JSONField(blank=True, default=list)
    correct_answer = models.JSONField(default=list)
    explanation = models.TextField()
    difficulty = models.PositiveSmallIntegerField(db_index=True, default=2, choices=[(1, '简单'), (2, '中等'), (3, '困难')])
    source_type = models.CharField(max_length=32, default='demo', choices=[('official_public', '官方公开'), ('authorized', '授权题目'), ('simulated', '模拟题'), ('demo', '演示题'), ('ai_assisted', 'AI辅助生成')])
    source = models.CharField(max_length=255, default='本地演示题')
    is_active = models.BooleanField(db_index=True, default=True)
    points = models.DecimalField(default=1, max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'core_question'
        ordering = ['id']
        indexes = [models.Index(name='core_questi_exam_ty_ffeae2_idx', fields=['exam_type', 'subject', 'difficulty', 'is_active'])]


class ExamPaper(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=20, db_index=True, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    subject = models.CharField(max_length=100, blank=True, db_index=True)
    total_questions = models.PositiveIntegerField(default=0)
    total_score = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=60)
    difficulty = models.CharField(max_length=20, default='mixed')
    blueprint = models.JSONField(blank=True, default=dict)
    is_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(blank=True, null=True, related_name='created_papers', on_delete=models.SET_NULL, to='core.user')

    class Meta:
        db_table = 'core_exampaper'
        ordering = ['-created_at']


class PaperQuestion(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    paper = models.ForeignKey(related_name='paper_questions', on_delete=models.CASCADE, to='core.exampaper')
    question = models.ForeignKey(related_name='paper_links', on_delete=models.PROTECT, to='core.question')
    order = models.PositiveIntegerField()
    points = models.DecimalField(default=1, max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'core_paperquestion'
        ordering = ['order']
        constraints = [models.UniqueConstraint(name='unique_paper_question', fields=('paper', 'question')), models.UniqueConstraint(name='unique_paper_order', fields=('paper', 'order'))]


class ExamAttempt(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='exam_attempts', on_delete=models.CASCADE, to='core.user')
    paper = models.ForeignKey(related_name='attempts', on_delete=models.PROTECT, to='core.exampaper')
    status = models.CharField(max_length=20, db_index=True, default='in_progress', choices=[('in_progress', '进行中'), ('submitted', '已提交'), ('expired', '超时提交')])
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    score = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    total_score = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    current_index = models.PositiveIntegerField(default=0)
    remaining_seconds = models.PositiveIntegerField(default=0)
    report = models.JSONField(blank=True, default=dict)
    submission_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        db_table = 'core_examattempt'
        ordering = ['-started_at']


class AnswerRecord(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attempt = models.ForeignKey(related_name='answers', on_delete=models.CASCADE, to='core.examattempt')
    question = models.ForeignKey(related_name='answer_records', on_delete=models.PROTECT, to='core.question')
    answer = models.JSONField(blank=True, default=list)
    is_marked = models.BooleanField(default=False)
    is_correct = models.BooleanField(blank=True, null=True)
    awarded_score = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    time_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'core_answerrecord'
        constraints = [models.UniqueConstraint(name='unique_attempt_answer', fields=('attempt', 'question'))]


class WrongQuestion(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='wrong_questions', on_delete=models.CASCADE, to='core.user')
    question = models.ForeignKey(related_name='wrong_users', on_delete=models.CASCADE, to='core.question')
    attempt_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    last_answered_at = models.DateTimeField(blank=True, null=True)
    average_time_seconds = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    mastered = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_wrongquestion'
        constraints = [models.UniqueConstraint(name='unique_user_wrong_question', fields=('user', 'question'))]


class WeaknessAnalysis(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(related_name='weakness_analyses', on_delete=models.CASCADE, to='core.user')
    exam_type = models.CharField(max_length=20, choices=[('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    subject = models.CharField(max_length=100)
    knowledge_point = models.ForeignKey(blank=True, null=True, related_name='weakness_records', on_delete=models.SET_NULL, to='core.knowledgepoint')
    completed_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    average_time_seconds = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    level = models.CharField(max_length=30, default='暂无数据')
    advice = models.TextField(blank=True)

    class Meta:
        db_table = 'core_weaknessanalysis'
        ordering = ['accuracy', '-completed_count']
        constraints = [models.UniqueConstraint(name='unique_weakness_dimension', fields=('user', 'exam_type', 'subject', 'knowledge_point'))]


class Notification(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(blank=True, null=True, related_name='notifications', on_delete=models.CASCADE, to='core.user')
    target = models.CharField(max_length=20, db_index=True, default='all', choices=[('all', '全部用户'), ('civil', '公务员'), ('institution', '事业单位'), ('graduate', '研究生')])
    notification_type = models.CharField(max_length=30, default='system', choices=[('announcement', '新公告'), ('registration_start', '报名开始'), ('registration_deadline', '报名截止'), ('payment', '缴费'), ('admission_ticket', '准考证打印'), ('exam', '考试时间'), ('system', '系统通知')])
    title = models.CharField(max_length=255)
    content = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(db_index=True, default=False)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(db_index=True, default=True)

    class Meta:
        db_table = 'core_notification'
        ordering = ['-created_at']


class NotificationReceipt(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notification = models.ForeignKey(related_name='receipts', on_delete=models.CASCADE, to='core.notification')
    user = models.ForeignKey(related_name='notification_receipts', on_delete=models.CASCADE, to='core.user')
    is_read = models.BooleanField(db_index=True, default=True)
    read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_notificationreceipt'
        ordering = ['-read_at', '-id']
        constraints = [models.UniqueConstraint(name='unique_notification_receipt_user', fields=('notification', 'user'))]


class ImportBatch(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(null=True, related_name='import_batches', on_delete=models.SET_NULL, to='core.user')
    import_type = models.CharField(max_length=40)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='processing', choices=[('processing', '处理中'), ('completed', '完成'), ('partial', '部分成功'), ('failed', '失败')])
    total_rows = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    error_report = models.JSONField(blank=True, default=list)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'core_importbatch'
        ordering = ['-created_at']


class SystemConfig(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.CharField(max_length=500, blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_systemconfig'


class AuditLog(models.Model):
    id = models.BigAutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)
    is_demo = models.BooleanField(verbose_name='演示数据', db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(blank=True, null=True, related_name='audit_logs', on_delete=models.SET_NULL, to='core.user')
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(blank=True, default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'core_auditlog'
        ordering = ['-created_at']


from .extensions import ServiceResource, ServiceRequest, ApplicationRecord

