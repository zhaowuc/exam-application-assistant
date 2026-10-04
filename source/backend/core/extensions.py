"""New public-services and application-data capabilities."""
from django.db import models
from django.conf import settings


class ServiceResource(models.Model):
    title = models.CharField('服务名称', max_length=180)
    category = models.CharField('分类', max_length=32, choices=[('guide', '办事指南'), ('faq', '常见问题'), ('materials', '材料清单'), ('portal', '官方入口')], default='guide')
    summary = models.CharField('简介', max_length=300, blank=True)
    content = models.TextField('内容')
    url = models.URLField('网址', blank=True)
    contact = models.CharField('联系信息', max_length=160, blank=True)
    exam_type = models.CharField('考试类型', max_length=20, default='all')
    is_active = models.BooleanField('启用', default=True)
    sort_order = models.PositiveIntegerField('排序', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']


class ServiceRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(ServiceResource, null=True, blank=True, on_delete=models.SET_NULL)
    subject = models.CharField('问题主题', max_length=180)
    content = models.TextField('问题描述')
    status = models.CharField('状态', max_length=20, default='pending', choices=[('pending', '待处理'), ('answered', '已回复'), ('closed', '已关闭')])
    response = models.TextField('回复', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ApplicationRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    opportunity = models.ForeignKey('core.Opportunity', on_delete=models.PROTECT)
    candidate_name = models.CharField('报考姓名', max_length=80)
    contact = models.CharField('联系方式', max_length=80, blank=True)
    status = models.CharField('报考状态', max_length=24, default='submitted', choices=[('draft', '草稿'), ('submitted', '已提交'), ('reviewing', '审核中'), ('approved', '审核通过'), ('rejected', '退回完善'), ('registered', '已报名'), ('completed', '已完成'), ('cancelled', '已取消')])
    materials = models.JSONField('材料清单', default=list, blank=True)
    notes = models.TextField('报考备注', blank=True)
    review_notes = models.TextField('审核说明', blank=True)
    score = models.DecimalField('考试成绩', max_digits=7, decimal_places=2, null=True, blank=True)
    result = models.CharField('录取结果', max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['user', 'opportunity'], name='unique_application_user_opportunity')]
