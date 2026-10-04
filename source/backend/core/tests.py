"""Regression suite for rebuilt modules. Runs against an isolated in-memory database."""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import tempfile
from django.test import TestCase,override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from . import models as m
from .registry import RESOURCES


class RebuildTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=m.User.objects.create_user('admin',password='Admin@123456',role='admin')
        cls.user=m.User.objects.create_user('tester',password='Test@123456')
        cls.other=m.User.objects.create_user('other',password='Other@123456')
        cls.profile=m.UserProfile.objects.create(user=cls.user,birth_year=2000,education='bachelor',degree='学士',major_text='计算机科学与技术',region='北京')
        cls.opp=m.Opportunity.objects.create(opportunity_type='civil',year=2026,region='北京',title='软件岗位',code='TEST1',organization='测试单位',major_requirement='不限',education_required='本科',max_age=35)
        m.CivilServicePosition.objects.create(opportunity=cls.opp,recruiting_agency='测试单位',employing_unit='测试单位')
        cls.category=m.QuestionCategory.objects.create(exam_type='civil',subject='行测',name='逻辑')
        cls.knowledge=m.KnowledgePoint.objects.create(category=cls.category,name='推理')
        cls.q=m.Question.objects.create(exam_type='civil',subject='行测',question_type='single',category=cls.category,knowledge_point=cls.knowledge,stem='1+1=?',options=[{'key':'A','text':'2'},{'key':'B','text':'3'}],correct_answer=['A'],explanation='一加一等于二',points=2)
        cls.q2=m.Question.objects.create(exam_type='civil',subject='行测',question_type='multiple',category=cls.category,knowledge_point=cls.knowledge,stem='哪些为偶数？',options=[{'key':'A','text':'2'},{'key':'B','text':'4'},{'key':'C','text':'3'}],correct_answer=['A','B'],explanation='2和4为偶数',points=3)
        cls.paper=m.ExamPaper.objects.create(title='测试试卷',exam_type='civil',total_questions=2,total_score=5,duration_minutes=10)
        m.PaperQuestion.objects.create(paper=cls.paper,question=cls.q,order=1,points=2)
        m.PaperQuestion.objects.create(paper=cls.paper,question=cls.q2,order=2,points=3)
        cls.resource=m.ServiceResource.objects.create(title='离线指南',content='指南正文')

    def setUp(self):
        self.client=APIClient()
        self.client.force_authenticate(self.user)
    def data(self,response,status=200):
        self.assertEqual(response.status_code,status,response.content[:1500])
        return response.json()['data']
    def start(self): return self.data(self.client.post('/api/v1/exams/start/',{'paper':self.paper.pk},format='json'),201)
    def admin_client(self): self.client.force_authenticate(self.admin)

    def test_public_health_and_home(self):
        self.client.force_authenticate(None)
        self.assertTrue(self.data(self.client.get('/api/v1/health/'))['offline'])
        self.assertEqual(self.data(self.client.get('/api/v1/home/'))['counts']['opportunities'],1)
    def test_login_and_bad_credentials(self):
        self.client.force_authenticate(None)
        data=self.data(self.client.post('/api/v1/auth/login/',{'username':'tester','password':'Test@123456'},format='json'))
        self.assertTrue(data['access'])
        self.assertNotIn('password',data['user'])
        self.assertEqual(self.client.post('/api/v1/auth/login/',{'username':'tester','password':'bad'}).status_code,401)
    def test_register_cannot_escalate_role(self):
        self.client.force_authenticate(None)
        data=self.data(self.client.post('/api/v1/auth/register/',{'username':'newuser','password':'Good@123456','role':'admin'},format='json'),201)
        self.assertEqual(data['user']['role'],'user')
        self.assertTrue(m.UserProfile.objects.filter(user_id=data['user']['id']).exists())
    def test_refresh_rotation_and_logout_revocation(self):
        self.client.force_authenticate(None)
        tokens=self.data(self.client.post('/api/v1/auth/login/',{'username':'tester','password':'Test@123456'}))
        self.data(self.client.post('/api/v1/auth/refresh/',{'refresh':tokens['refresh']}))
        self.assertEqual(self.client.post('/api/v1/auth/refresh/',{'refresh':tokens['refresh']}).status_code,401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+tokens['access'])
        self.data(self.client.post('/api/v1/auth/logout/',{}))
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code,401)
    def test_password_change_invalidates_access(self):
        self.client.force_authenticate(None)
        tokens=self.data(self.client.post('/api/v1/auth/login/',{'username':'tester','password':'Test@123456'}))
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+tokens['access'])
        self.data(self.client.post('/api/v1/auth/change-password/',{'old_password':'Test@123456','new_password':'Changed@123456'}))
        self.assertEqual(self.client.get('/api/v1/profile/').status_code,401)
    def test_profile_validation(self):
        self.assertEqual(self.client.patch('/api/v1/profile/',{'birth_year':9999},format='json').status_code,400)
        self.assertEqual(self.client.patch('/api/v1/profile/',{'mock_scores':[]},format='json').status_code,400)
        self.data(self.client.patch('/api/v1/profile/',{'certificates':['测试证书']},format='json'))
    def test_admin_access_denied(self):
        self.assertEqual(self.client.get('/api/v1/admin/dashboard/').status_code,403)
        self.assertEqual(self.client.get('/api/v1/admin/questions/').status_code,403)
    def test_all_admin_resources_and_schemas(self):
        self.admin_client()
        for name in RESOURCES:
            with self.subTest(resource=name):
                self.data(self.client.get(f'/api/v1/admin/{name}/'))
                self.data(self.client.get(f'/api/v1/admin/{name}/schema/'))
    def test_protect_current_admin(self):
        self.admin_client()
        self.assertEqual(self.client.patch(f'/api/v1/admin/users/{self.admin.pk}/',{'status':'disabled'},format='json').status_code,400)
        self.assertEqual(self.client.delete(f'/api/v1/admin/users/{self.admin.pk}/').status_code,400)
    def test_user_cannot_edit_role(self):
        self.data(self.client.patch('/api/v1/auth/me/',{'role':'admin'},format='json'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.role,'user')
    def test_catalog_filter_history_matching(self):
        rows=self.data(self.client.get('/api/v1/opportunities/?search=软件&opportunity_type=civil'))
        self.assertEqual(rows['count'],1)
        self.assertEqual(self.data(self.client.get(f'/api/v1/opportunities/{self.opp.pk}/matching/'))['status'],'eligible')
        self.data(self.client.get(f'/api/v1/opportunities/{self.opp.pk}/history/'))
    def test_recommendations_and_weight_changes(self):
        data=self.data(self.client.post('/api/v1/recommendations/',{},format='json'))
        self.assertEqual(data['count'],1)
        self.assertEqual(m.RecommendationRecord.objects.count(),1)
        m.RecommendationRule.objects.create(exam_type='civil',name='名额',key='capacity',weight=100)
        data=self.data(self.client.get('/api/v1/recommendations/'))
        self.assertGreater(data['results'][0]['breakdown']['slots']['weight'],40)
    def test_matching_excludes_ineligible(self):
        self.opp.max_age=20;self.opp.save()
        self.assertEqual(self.data(self.client.get('/api/v1/recommendations/'))['count'],0)
    def test_public_services_and_user_ticket(self):
        self.assertEqual(self.data(self.client.get('/api/v1/services/'))['count'],1)
        obj=self.data(self.client.post('/api/v1/service-requests/',{'subject':'咨询','content':'如何准备？','resource':self.resource.pk},format='json'),201)
        self.assertEqual(obj['user'],self.user.pk)
        self.assertEqual(self.client.patch(f"/api/v1/service-requests/{obj['id']}/",{'response':'伪造回复'},format='json').status_code,400)
    def test_ticket_reply_and_notice(self):
        obj=m.ServiceRequest.objects.create(user=self.user,subject='咨询',content='问题')
        self.admin_client()
        self.data(self.client.patch(f'/api/v1/admin/service-requests/{obj.pk}/',{'status':'answered','response':'已回复'},format='json'))
        self.assertTrue(m.Notification.objects.filter(user=self.user).exists())
    def test_applications_duplicate_and_permissions(self):
        body={'opportunity':self.opp.pk,'candidate_name':'测试同学','materials':['学历证明']}
        row=self.data(self.client.post('/api/v1/applications/',body,format='json'),201)
        self.assertEqual(self.client.post('/api/v1/applications/',body,format='json').status_code,400)
        self.assertEqual(self.client.patch(f"/api/v1/applications/{row['id']}/",{'status':'approved'},format='json').status_code,400)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/applications/{row['id']}/").status_code,404)
        self.assertEqual(self.data(self.client.get('/api/v1/applications/'))['count'],0)
    def test_application_review_and_filter(self):
        obj=m.ApplicationRecord.objects.create(user=self.user,opportunity=self.opp,candidate_name='测试')
        self.admin_client()
        self.data(self.client.patch(f'/api/v1/admin/applications/{obj.pk}/',{'status':'approved','review_notes':'材料齐全','score':'88.5','result':'已录取'},format='json'))
        data=self.data(self.client.get('/api/v1/admin/applications/?exam_type=graduate'))
        self.assertEqual(data['count'],0)
        self.assertEqual(self.data(self.client.get('/api/v1/admin/applications/?year=2026&status=approved'))['count'],1)
    def test_application_deletion_control(self):
        row=m.ApplicationRecord.objects.create(user=self.user,opportunity=self.opp,candidate_name='测试')
        self.assertEqual(self.client.delete(f'/api/v1/applications/{row.pk}/').status_code,400)
        self.data(self.client.patch(f'/api/v1/applications/{row.pk}/',{'status':'cancelled'},format='json'))
        self.assertEqual(self.client.delete(f'/api/v1/applications/{row.pk}/').status_code,204)
    def test_rejected_application_can_resubmit(self):
        row=m.ApplicationRecord.objects.create(user=self.user,opportunity=self.opp,candidate_name='测试',status='rejected')
        data=self.data(self.client.patch(f'/api/v1/applications/{row.pk}/',{'candidate_name':'修订姓名','materials':['学历证明'],'status':'submitted'},format='json'))
        self.assertEqual(data['status'],'submitted')
        self.admin_client()
        self.assertEqual(self.client.patch(f'/api/v1/admin/applications/{row.pk}/',{'score':-5},format='json').status_code,400)
    def test_structured_major_rule(self):
        m.RequirementRule.objects.create(opportunity=self.opp,field_name='major',label='专项专业目录',operator='major',expected_value=['计算机科学与技术'])
        self.assertEqual(self.data(self.client.get(f'/api/v1/opportunities/{self.opp.pk}/matching/'))['status'],'eligible')
    def test_favorites_comparison_and_ownership(self):
        self.data(self.client.post('/api/v1/favorites/',{'opportunity':self.opp.pk},format='json'),201)
        self.assertEqual(self.client.post('/api/v1/favorites/',{'opportunity':self.opp.pk},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/v1/comparisons/',{'opportunities':[self.opp.pk]},format='json').status_code,400)
        other=m.Opportunity.objects.create(opportunity_type='civil',year=2026,region='北京',title='第二岗位',code='TEST2')
        row=self.data(self.client.post('/api/v1/comparisons/',{'opportunities':[self.opp.pk,other.pk]},format='json'),201)
        self.assertEqual(len(row['snapshot']['opportunities']),2)
    def test_plan_and_reminder_receipts(self):
        self.data(self.client.post('/api/v1/application-plans/',{'title':'考试计划','exam_date':str(timezone.localdate()+timedelta(days=1))},format='json'),201)
        rows=self.data(self.client.get('/api/v1/notifications/'))['results']
        self.assertEqual(len(rows),1)
        self.assertFalse(rows[0]['is_read'])
        self.data(self.client.post(f"/api/v1/notifications/{rows[0]['id']}/read/",{}))
        self.assertTrue(self.data(self.client.get('/api/v1/notifications/'))['results'][0]['is_read'])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.data(self.client.get('/api/v1/notifications/'))['count'],0)
    def test_safe_question_and_paper_no_keys(self):
        row=self.data(self.client.get(f'/api/v1/questions/{self.q.pk}/'))
        self.assertNotIn('correct_answer',row);self.assertNotIn('explanation',row)
        paper=self.data(self.client.get(f'/api/v1/papers/{self.paper.pk}/'))
        self.assertNotIn('correct_answer',paper['questions'][0])
    def test_practice_answer(self):
        row=self.data(self.client.post(f'/api/v1/questions/{self.q.pk}/practice/',{'answer':['A']},format='json'))
        self.assertTrue(row['is_correct']);self.assertTrue(row['explanation'])
    def test_generate_insufficient_and_success(self):
        self.assertEqual(self.client.post('/api/v1/papers/generate/',{'count':3},format='json').status_code,400)
        row=self.data(self.client.post('/api/v1/papers/generate/',{'count':2},format='json'),201)
        self.assertEqual(len(row['questions']),2)
    def test_exam_save_resume_and_no_answer_key(self):
        row=self.start()
        self.assertNotIn('correct_answer',row['questions'][0])
        self.data(self.client.post(f"/api/v1/attempts/{row['id']}/save/",{'answers':[{'question':self.q.pk,'answer':['A']}],'current_index':1},format='json'))
        restored=self.data(self.client.get(f"/api/v1/attempts/{row['id']}/"))
        self.assertEqual(restored['answers'][0]['answer'],['A'])
        self.assertEqual(restored['current_index'],1)
    def test_exam_grade_full_multiple_and_idempotent(self):
        row=self.start();url=f"/api/v1/attempts/{row['id']}/submit/"
        data=self.data(self.client.post(url,{'answers':[{'question':self.q.pk,'answer':['A']},{'question':self.q2.pk,'answer':['B','A']}]},format='json'))
        self.assertEqual(Decimal(data['score']),5)
        self.assertEqual(data['correct_count'],2)
        self.assertTrue(data['report']['details'][0]['correct_answer'])
        self.data(self.client.post(url,{},format='json'))
        self.assertEqual(m.WeaknessAnalysis.objects.get(user=self.user).completed_count,2)
    def test_wrong_and_weakness(self):
        row=self.start()
        data=self.data(self.client.post(f"/api/v1/attempts/{row['id']}/submit/",{'answers':[{'question':self.q.pk,'answer':['B']},{'question':self.q2.pk,'answer':['A']}]},format='json'))
        self.assertEqual(Decimal(data['score']),0)
        self.assertEqual(m.WrongQuestion.objects.filter(user=self.user).count(),2)
        self.assertEqual(self.data(self.client.get('/api/v1/weakness/'))[0]['completed_count'],2)
        self.data(self.client.get('/api/v1/scores/'))
    def test_expired_exam_discards_late_answer(self):
        row=self.start();m.ExamAttempt.objects.filter(pk=row['id']).update(expires_at=timezone.now()-timedelta(seconds=1))
        data=self.data(self.client.post(f"/api/v1/attempts/{row['id']}/save/",{'answers':[{'question':self.q.pk,'answer':['A']}]},format='json'))
        self.assertEqual(data['status'],'expired');self.assertEqual(Decimal(data['score']),0)
    def test_exam_foreign_question_and_ownership(self):
        row=self.start()
        self.assertEqual(self.client.post(f"/api/v1/attempts/{row['id']}/save/",{'answers':[{'question':999,'answer':['A']}]},format='json').status_code,400)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/attempts/{row['id']}/").status_code,404)
    def test_exam_blocks_live_question_edits(self):
        self.start();self.admin_client()
        self.assertEqual(self.client.patch(f'/api/v1/admin/questions/{self.q.pk}/',{'correct_answer':['B']},format='json').status_code,400)
        self.assertEqual(self.client.delete(f'/api/v1/admin/paper-questions/{self.paper.paper_questions.first().pk}/').status_code,400)
    def test_invalid_question_and_opportunity(self):
        self.admin_client()
        self.assertEqual(self.client.patch(f'/api/v1/admin/questions/{self.q.pk}/',{'correct_answer':['Z']},format='json').status_code,400)
        self.assertEqual(self.client.patch(f'/api/v1/admin/opportunities/{self.opp.pk}/',{'min_age':80},format='json').status_code,400)
    def test_notices_services_crud_and_audit(self):
        self.admin_client()
        row=self.data(self.client.post('/api/v1/admin/services/',{'title':'新指南','content':'服务正文'},format='json'),201)
        self.data(self.client.patch(f"/api/v1/admin/services/{row['id']}/",{'title':'修改指南'},format='json'))
        self.assertEqual(self.client.delete(f"/api/v1/admin/services/{row['id']}/").status_code,204)
        self.assertEqual(m.AuditLog.objects.count(),3)
    def test_import_export_template_errors(self):
        from openpyxl import Workbook
        self.admin_client()
        for suffix in ['export','template']:
            response=self.client.get(f'/api/v1/admin/services/{suffix}/')
            self.assertEqual(response.status_code,200)
            self.assertTrue(b''.join(response.streaming_content).startswith(b'PK'))
        book=Workbook();sheet=book.active;sheet.append(['title','content']);sheet.append(['导入指南','正文']);sheet.append(['坏记录',None]);stream=BytesIO();book.save(stream)
        upload=SimpleUploadedFile('test.xlsx',stream.getvalue())
        row=self.data(self.client.post('/api/v1/admin/services/import/',{'file':upload},format='multipart'))
        self.assertEqual(row['success_count'],1);self.assertEqual(row['failure_count'],1);self.assertEqual(row['error_report'][0]['row'],3)
    def test_readonly_resource_cannot_modify(self):
        self.admin_client()
        self.assertEqual(self.client.post('/api/v1/admin/audit-logs/',{'action':'fake'},format='json').status_code,400)
    def test_import_paper_link_updates_totals(self):
        from openpyxl import Workbook
        paper=m.ExamPaper.objects.create(title='导入编排',exam_type='civil')
        self.admin_client()
        book=Workbook();sheet=book.active;sheet.append(['paper','question','order','points']);sheet.append([paper.pk,self.q.pk,1,3]);stream=BytesIO();book.save(stream)
        row=self.data(self.client.post('/api/v1/admin/paper-questions/import/',{'file':SimpleUploadedFile('links.xlsx',stream.getvalue())},format='multipart'))
        self.assertEqual(row['success_count'],1)
        paper.refresh_from_db();self.assertEqual(paper.total_questions,1);self.assertEqual(paper.total_score,3)
    def test_restore_requires_confirmation_and_valid_db(self):
        self.admin_client()
        response=self.client.post('/api/v1/admin/restore/',{'confirm':'NO'},format='multipart')
        self.assertEqual(response.status_code,400)
        bad=SimpleUploadedFile('bad.sqlite3',b'not a database')
        self.assertEqual(self.client.post('/api/v1/admin/restore/',{'confirm':'RESTORE','file':bad},format='multipart').status_code,400)
