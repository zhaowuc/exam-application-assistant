from rest_framework.renderers import JSONRenderer
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError


class EnvelopeRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get('response')
        error = response is not None and response.status_code >= 400
        return super().render({
            'success': not error, 'code': response.status_code if error else 0,
            'message': str(data.get('detail', '请检查填写内容')) if error and isinstance(data, dict) else ('请求失败' if error else '请求成功'),
            'data': None if error else data, 'errors': data if error else None,
        }, accepted_media_type, renderer_context)


class Pagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


def exception_handler(exc, context):
    from rest_framework.views import exception_handler as drf_handler
    if isinstance(exc, IntegrityError):
        exc = ValidationError('记录重复或关联数据无效，请检查后重试。')
    elif isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.messages)
    elif isinstance(exc, (ValueError, TypeError)):
        exc = ValidationError('字段或筛选参数类型不正确。')
    return drf_handler(exc, context)
