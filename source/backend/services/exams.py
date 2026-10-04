"""Server-authoritative exam lifecycle. Answer keys are released only after grading."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core import models as m
from core.serializers import SafeQuestionSerializer


def normalize(value):
    if not isinstance(value, list) or any(not isinstance(v, (str, bool, int)) for v in value):
        raise ValidationError('答案应为选项标识数组。')
    return sorted(set(str(v) for v in value))


@transaction.atomic
def start(user, paper):
    links = list(paper.paper_questions.select_related('question'))
    if not links or any(not link.question.is_active for link in links):
        raise ValidationError('试卷为空或包含已停用题目。')
    if not 1 <= paper.duration_minutes <= 600:
        raise ValidationError('考试时长应为 1–600 分钟。')
    attempt = m.ExamAttempt.objects.create(user=user, paper=paper,
        expires_at=timezone.now()+timedelta(minutes=paper.duration_minutes),
        total_score=sum((link.points for link in links), Decimal(0)), remaining_seconds=paper.duration_minutes*60)
    m.AnswerRecord.objects.bulk_create([m.AnswerRecord(attempt=attempt, question=link.question) for link in links])
    return attempt


@transaction.atomic
def save(attempt, payload):
    attempt = m.ExamAttempt.objects.select_for_update().get(pk=attempt.pk)
    if attempt.status != 'in_progress':
        raise ValidationError('此考试已交卷，不能继续修改答案。')
    if timezone.now() >= attempt.expires_at:
        return grade(attempt, expired=True)
    answers = payload.get('answers', [])
    if not isinstance(answers, list) or len(answers) > 500:
        raise ValidationError('无效的答题记录。')
    available = {row.question_id: row for row in attempt.answers.select_related('question')}
    for item in answers:
        if not isinstance(item, dict) or item.get('question') not in available:
            raise ValidationError('题目不属于当前考试。')
        row = available[item['question']]
        value = normalize(item.get('answer', []))
        options = row.question.options
        valid = [str(o.get('key', o.get('id', ''))) if isinstance(o, dict) else str(i) for i, o in enumerate(options)]
        if options and any(v not in valid for v in value):
            raise ValidationError('答案包含不存在的选项。')
        if row.question.question_type != 'multiple' and len(value) > 1:
            raise ValidationError('单选和判断题只能选择一个答案。')
        row.answer = value
        row.is_marked = bool(item.get('is_marked', False))
        try:
            row.time_seconds = min(36000, max(0, int(item.get('time_seconds', row.time_seconds))))
        except (ValueError, TypeError):
            raise ValidationError('答题时间无效。')
        row.save(update_fields=['answer', 'is_marked', 'time_seconds', 'updated_at'])
    try:
        attempt.current_index = max(0, min(len(available)-1, int(payload.get('current_index', attempt.current_index))))
    except (ValueError, TypeError):
        raise ValidationError('题目索引无效。')
    attempt.remaining_seconds = max(0, int((attempt.expires_at-timezone.now()).total_seconds()))
    attempt.save(update_fields=['current_index', 'remaining_seconds', 'updated_at'])
    return attempt


@transaction.atomic
def grade(attempt, expired=False):
    attempt = m.ExamAttempt.objects.select_for_update().get(pk=attempt.pk)
    if attempt.status != 'in_progress':
        return attempt
    links = {link.question_id: link for link in attempt.paper.paper_questions.all()}
    correct = incorrect = unanswered = 0
    score = Decimal(0)
    details = []
    for row in attempt.answers.select_related('question__knowledge_point'):
        question = row.question
        row.is_correct = bool(row.answer) and normalize(row.answer) == normalize(question.correct_answer)
        row.awarded_score = links[row.question_id].points if row.is_correct else Decimal(0)
        score += row.awarded_score
        correct += int(row.is_correct)
        incorrect += int(bool(row.answer) and not row.is_correct)
        unanswered += int(not row.answer)
        row.save(update_fields=['is_correct', 'awarded_score', 'updated_at'])
        wrong = m.WrongQuestion.objects.filter(user=attempt.user, question=question).first()
        if wrong or not row.is_correct:
            wrong = wrong or m.WrongQuestion(user=attempt.user, question=question)
            wrong.average_time_seconds = (wrong.average_time_seconds*wrong.attempt_count+row.time_seconds)/(wrong.attempt_count+1)
            wrong.attempt_count += 1
            wrong.correct_count += int(row.is_correct)
            wrong.wrong_count += int(not row.is_correct)
            wrong.last_answered_at = timezone.now()
            if not row.is_correct:
                wrong.mastered = False
            wrong.save()
        details.append({'question': question.id, 'stem': question.stem, 'options': question.options,
            'answer': row.answer, 'correct_answer': question.correct_answer, 'explanation': question.explanation,
            'is_correct': row.is_correct, 'awarded_score': str(row.awarded_score),
            'knowledge_name': question.knowledge_point.name})
    attempt.status = 'expired' if expired or timezone.now() >= attempt.expires_at else 'submitted'
    attempt.submitted_at = timezone.now()
    attempt.duration_seconds = min(attempt.paper.duration_minutes*60, max(0, int((attempt.submitted_at-attempt.started_at).total_seconds())))
    attempt.score = score
    attempt.correct_count, attempt.incorrect_count, attempt.unanswered_count = correct, incorrect, unanswered
    attempt.remaining_seconds = 0
    attempt.report = {'details': details, 'accuracy': round(correct/max(1, len(details))*100, 2), 'summary': '多选题全部选对才得分；未作答计零分。'}
    attempt.save()
    rebuild_weakness(attempt.user)
    return attempt


def rebuild_weakness(user):
    groups = defaultdict(list)
    for row in m.AnswerRecord.objects.filter(attempt__user=user).exclude(attempt__status='in_progress').select_related('question'):
        groups[(row.question.exam_type, row.question.subject, row.question.knowledge_point_id)].append(row)
    for (exam_type, subject, knowledge), rows in groups.items():
        count = len(rows)
        correct = sum(bool(row.is_correct) for row in rows)
        accuracy = round(correct/count*100, 2)
        m.WeaknessAnalysis.objects.update_or_create(user=user, exam_type=exam_type, subject=subject, knowledge_point_id=knowledge,
            defaults={'completed_count':count, 'correct_count':correct, 'accuracy':accuracy,
                'average_time_seconds':sum(row.time_seconds for row in rows)/count,
                'level':'薄弱' if accuracy < 60 else '待提升' if accuracy < 85 else '熟练',
                'advice':'回顾解析并进行专项练习。' if accuracy < 85 else '定期复习，保持熟练度。'})


def represent(attempt):
    if attempt.status == 'in_progress' and timezone.now() >= attempt.expires_at:
        attempt = grade(attempt, expired=True)
    from core.serializers import model_serializer
    result = model_serializer(m.ExamAttempt)(attempt).data
    result['paper_title'] = attempt.paper.title
    result['remaining_seconds'] = max(0, int((attempt.expires_at-timezone.now()).total_seconds())) if attempt.status == 'in_progress' else 0
    result['questions'] = [{**SafeQuestionSerializer(link.question).data, 'paper_points':str(link.points)} for link in attempt.paper.paper_questions.select_related('question__knowledge_point')]
    result['answers'] = [{'question':row.question_id, 'answer':row.answer, 'is_marked':row.is_marked, 'time_seconds':row.time_seconds} for row in attempt.answers.all()]
    return result
