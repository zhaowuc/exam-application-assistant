"""Deterministic local qualification matching with explicit uncertainty."""
import re
import unicodedata
from django.utils import timezone
from core.models import Major, RecommendationRule

EDUCATION = {'high_school': 1, 'college': 2, 'bachelor': 3, 'master': 4, 'doctor': 5}
EDU_ZH = {'高中': 1, '大专': 2, '专科': 2, '本科': 3, '硕士': 4, '研究生': 4, '博士': 5}
LABELS = {'eligible': '符合', 'ineligible': '不符合', 'possible': '待完善', 'manual_review': '需人工确认'}

def text(value):
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(value or '')))

def major_status(requirement,major,major_name):
    if isinstance(requirement,dict): requirement=requirement.get('majors',requirement.get('value',[]))
    allowed=[text(x) for x in requirement] if isinstance(requirement,list) else [text(x) for x in re.split(r'[、,，;；/\n]',str(requirement))]
    if not any(allowed) or any(x in ['不限','专业不限'] for x in allowed): return 'eligible'
    if not major_name:return 'possible'
    names=[major_name]
    if major:
        names+=major.aliases+[major.category.name]
        if major.category.parent:names.append(major.category.parent.name)
    if any(text(x) in allowed for x in names):return 'eligible'
    if major and any(text(x) in allowed for x in major.related_names):return 'possible'
    if any(x in str(requirement) for x in ['相关','相近','认定','参照']):return 'manual_review'
    return 'ineligible'


def match(opportunity, profile):
    checks = []
    def add(label, got, wanted, status, reason, hard=True):
        checks.append({'label': label, 'value': got, 'expected': wanted, 'status': status, 'reason': reason, 'is_hard': hard})
    def test(label, got, wanted, predicate):
        if wanted in ('', None, '不限', [], '专业不限'):
            return add(label, got, wanted, 'eligible', '不限制此项')
        if got is None or got == '':
            return add(label, got, wanted, 'possible', '请完善个人档案后再次匹配')
        passed = predicate(got, wanted)
        add(label, got, wanted, 'eligible' if passed else 'ineligible', '满足条件' if passed else f'当前 {got}，要求 {wanted}')
    required = opportunity.education_required
    if required not in ('', '不限'):
        level = next((v for k, v in EDU_ZH.items() if k in required), None)
        if level:
            test('学历', profile.get('education'), required, lambda a, b: EDUCATION.get(a, 0) >= level if '仅' not in b else EDUCATION.get(a, 0) == level)
        else:
            add('学历', profile.get('education'), required, 'manual_review', '非标准学历描述，需要人工核对')
    test('学位', profile.get('degree'), opportunity.degree_required, lambda a, b: a == b or a in b)
    major_requirement = opportunity.major_requirement
    major = Major.objects.filter(pk=profile.get('major')).select_related('category__parent').first() if profile.get('major') else None
    major_name = major.name if major else profile.get('major_text', '')
    if major_requirement in ('', '不限', '专业不限'):
        add('专业', major_name, major_requirement, 'eligible', '专业不限')
    elif not major_name:
        add('专业', '', major_requirement, 'possible', '请填写专业')
    else:
        allowed = [x.strip() for x in re.split(r'[、,，;；/\n]', major_requirement)]
        candidates = [major_name]
        if major:
            candidates += major.aliases + [major.category.name]
            if major.category.parent:
                candidates.append(major.category.parent.name)
        exact = any(x in allowed for x in candidates)
        related = major and any(x in allowed for x in major.related_names)
        uncertain = any(x in major_requirement for x in ('相关', '相近', '认定', '参照'))
        status = 'eligible' if exact else ('possible' if related else ('manual_review' if uncertain else 'ineligible'))
        add('专业', major_name, major_requirement, status, '命中专业或目录分类' if exact else '需核对公告专业目录' if related or uncertain else '不在明确列举的专业范围')
    age = timezone.localdate().year - int(profile['birth_year']) if profile.get('birth_year') else None
    test('年龄上限', age, opportunity.max_age, lambda a, b: a <= b)
    if opportunity.min_age:
        test('年龄下限', age, opportunity.min_age, lambda a, b: a >= b)
    for field, label in [('work_years', '工作年限'), ('grassroots_years', '基层年限')]:
        test(label, profile.get(field), getattr(opportunity, field), lambda a, b: float(a) >= float(b))
    if opportunity.fresh_graduate_requirement != 'unrestricted':
        test('应届身份', profile.get('is_fresh_graduate'), opportunity.fresh_graduate_requirement == 'required', lambda a, b: a == b)
    test('政治面貌', profile.get('political_status'), opportunity.political_status, lambda a, b: a == b or a in b)
    test('户籍', profile.get('household_region'), opportunity.household_requirement, lambda a, b: a == b or a in b)
    test('资格证书', profile.get('certificates', []), opportunity.certificates_required, lambda a, b: set(b).issubset(set(a)))
    if opportunity.other_conditions:
        add('其他条件', '', opportunity.other_conditions, 'manual_review', '请向招录单位核对证明材料要求')
    if opportunity.opportunity_type=='graduate':
        try:
            detail=opportunity.graduate_detail
            result=major_status(detail.bachelor_major_requirement,major,major_name)
            add('本科专业要求',major_name,detail.bachelor_major_requirement,result,LABELS[result])
            if detail.cross_major_requirement and detail.cross_major_requirement not in ['允许跨考','不限']:
                add('跨考要求',major_name,detail.cross_major_requirement,'manual_review','请核对院校招生简章的跨考口径')
        except AttributeError:pass
    operators = {'eq': lambda a,b:a==b, 'in':lambda a,b:a in b, 'gte':lambda a,b:float(a)>=float(b), 'lte':lambda a,b:float(a)<=float(b), 'contains':lambda a,b:all(x in a for x in b) if isinstance(b,list) else b in a}
    for rule in opportunity.requirement_rules.filter(is_active=True).order_by('sort_order'):
        got = age if rule.field_name == 'age' else profile.get(rule.field_name)
        status = 'manual_review'
        try:
            if rule.operator=='major':
                status=major_status(rule.expected_value,major,major_name)
            elif rule.operator in operators and got is not None:
                status = 'eligible' if operators[rule.operator](got, rule.expected_value) else 'ineligible'
            elif got is None and rule.operator != 'manual':
                status = 'possible'
        except (TypeError, ValueError):
            pass
        add(rule.label, got, rule.expected_value, status, '附加规则：'+LABELS[status], rule.is_hard)
    states = {x['status'] for x in checks if x['is_hard']}
    status = next((s for s in ['ineligible', 'manual_review', 'possible'] if s in states), 'eligible')
    return {'status': status, 'label': LABELS[status], 'checks': checks, 'summary': '算法仅供辅助，请以官方资格审查结果为准。'}


def recommend(opportunity, profile):
    qualification = match(opportunity, profile)
    if qualification['status'] == 'ineligible':
        return None
    regions = profile.get('target_regions', [])
    score_value = profile.get('mock_scores', {}).get(opportunity.opportunity_type)
    ratio = opportunity.competition_ratio
    dimensions = {
        'qualification': 100 if qualification['status']=='eligible' else 70,
        'major': next((100 if c['status']=='eligible' else 60 for c in qualification['checks'] if c['label']=='专业'),70),
        'region': 100 if not regions or opportunity.region in regions else 40,
        'slots': min(100, 50 + opportunity.slots * 5),
        'competition': max(10, 100 - ratio) if opportunity.approved_count else 50,
        'score': max(0, min(100, 70 + (float(score_value)-float(opportunity.lowest_score))*2)) if score_value is not None and opportunity.lowest_score else 50,
        'school':100 if not profile.get('school_preferences') or opportunity.organization in profile.get('school_preferences',[]) else 40,
    }
    weights={'qualification':40,'major':15,'region':15,'slots':10,'competition':10,'score':10,'school':0}
    mapping={'qualification':'qualification','major':'major','region':'region','capacity':'slots','competition':'competition','history_score':'score','school':'school'}
    for rule in RecommendationRule.objects.filter(exam_type=opportunity.opportunity_type,is_active=True):
        if rule.key in mapping and rule.weight>=0:
            weights[mapping[rule.key]]=float(rule.weight)
    total=sum(weights.values()) or 100
    breakdown={k:{'score':v,'weight':round(weights[k]/total*100,2),'contribution':round(v*weights[k]/total,2)} for k,v in dimensions.items()}
    score=round(sum(x['contribution'] for x in breakdown.values()),2)
    level='sprint' if dimensions['competition']<40 or dimensions['score']<50 else ('safe' if score>=85 else 'steady')
    return {'score':score,'level':level,'qualification_status':qualification['status'],'breakdown':breakdown,'strengths':[c['label']+'符合' for c in qualification['checks'] if c['status']=='eligible'], 'risks':[c['reason'] for c in qualification['checks'] if c['status']!='eligible']+(['缺少历史报名数据'] if not opportunity.approved_count else []),'advice':'结合官方公告、个人成绩和材料要求选择报考目标。','explanation':'依据档案、资格规则及本地历史数据计算，不代表录取概率。'}
