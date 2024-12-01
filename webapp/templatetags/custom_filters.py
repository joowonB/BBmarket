from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def time_since(value):
    """
    시간 차이를 계산하여 문자열로 반환합니다.
    예: 2시간 전, 1일 전 등
    """
    if not isinstance(value, timezone.datetime):
        return value
    
    now = timezone.now()
    diff = now - value

    if diff.days > 0:
        return f"{diff.days}일전"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}시간전"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}분전"
    else:
        return "방금 전"
