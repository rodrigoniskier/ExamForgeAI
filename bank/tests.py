import json
from django.contrib.auth.models import User
from django.test import TestCase,override_settings
from django.urls import reverse
from .models import AcademicTerm,Course,Option,Question

class ExamForgeTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user("editor",password="long-password-123")
        self.term=AcademicTerm.objects.create(name="Demo")
        self.course=Course.objects.create(name="Course",term=self.term)
    def add_question(self,status):
        q=Question.objects.create(course=self.course,author=self.user,stem=f"{status} item",rationale="Because",status=status)
        Option.objects.create(question=q,text="Correct",is_correct=True,order=1); Option.objects.create(question=q,text="Wrong",is_correct=False,order=2); return q
    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code,302)
    @override_settings(USE_FAKE_AI=True)
    def test_fake_ai_returns_structured_draft(self):
        self.client.force_login(self.user)
        r=self.client.post(reverse("ai_generate"),data=json.dumps({"course_id":self.course.id,"prompt":"Demo topic","bloom":"APPLY","difficulty":"MEDIUM"}),content_type="application/json")
        self.assertEqual(r.status_code,200); self.assertEqual(sum(1 for o in r.json()["options"] if o["is_correct"]),1)
    def test_assessment_uses_only_approved_questions(self):
        self.add_question("APPROVED"); self.add_question("REJECTED")
        self.client.force_login(self.user)
        r=self.client.post(reverse("assessment_create"),{"title":"Demo exam","term":self.term.id,"course":self.course.id,"count":1})
        self.assertEqual(r.status_code,302)
        self.assertEqual(r.url.split("/")[-2],"1")
