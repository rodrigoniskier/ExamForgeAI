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

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

@override_settings(PORTFOLIO_DEMO=True)
class PortfolioDemoTests(TestCase):
    def setUp(self):
        call_command("seed_demo",verbosity=0)
    def test_seed_is_idempotent_and_has_no_privileged_account(self):
        from django.contrib.auth.models import User
        before=User.objects.count()
        call_command("seed_demo",verbosity=0)
        self.assertEqual(User.objects.count(),before)
        self.assertFalse(User.objects.filter(is_staff=True).exists())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())
    def test_demo_entry_and_admin_boundary(self):
        name=settings.DEMO_ACCOUNTS[0][0]
        self.assertEqual(self.client.post("/demo/enter/",{"account":name}).status_code,302)
        self.assertEqual(self.client.get("/").status_code,200)
        self.assertEqual(self.client.get("/admin/").status_code,403)
        self.assertEqual(self.client.post("/demo/enter/",{"account":"admin"}).status_code,404)
    def test_demo_login_requires_csrf(self):
        from django.test import Client
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/demo/enter/",{"account":settings.DEMO_ACCOUNTS[0][0]}).status_code,403)

    def test_seed_edit_creates_independent_copy_with_options(self):
        self.client.post("/demo/enter/",{"account":"editor.demo"})
        q=Question.objects.filter(status="APPROVED").first()
        original=q.stem
        payload={"course":q.course_id,"question_type":"SINGLE","context":q.context,"stem":"Versão revisada do item fictício","rationale":q.rationale,"bloom":q.bloom,"difficulty":q.difficulty,"primary_area":q.primary_area,"competency":q.competency,"status":"PENDING","proposition_two":"","review_comment":"Revisado por uma pessoa.","options-TOTAL_FORMS":"4","options-INITIAL_FORMS":"0","options-MIN_NUM_FORMS":"2","options-MAX_NUM_FORMS":"1000"}
        for i,o in enumerate(q.options.all()):
            payload[f"options-{i}-text"]=o.text
            payload[f"options-{i}-order"]=str(i+1)
            if o.is_correct:payload[f"options-{i}-is_correct"]="on"
        r=self.client.post(f"/questions/{q.pk}/edit/",payload)
        self.assertEqual(r.status_code,302)
        q.refresh_from_db();self.assertEqual(q.stem,original)
        copy=Question.objects.get(stem="Versão revisada do item fictício")
        self.assertEqual(copy.options.count(),4)
        self.assertEqual(copy.status,"PENDING")
    def test_fake_mode_prevents_network_even_with_real_mode_flag(self):
        from unittest.mock import patch
        from bank.ai import generate_question
        with override_settings(USE_FAKE_AI=False), patch("bank.ai.requests.post") as network:
            draft=generate_question("processos", "Gestão", {})
        network.assert_not_called()
        self.assertTrue(draft["demo"])
    def test_answer_key_uses_letters(self):
        self.client.post("/demo/enter/",{"account":"editor.demo"})
        response=self.client.get("/assessments/1/")
        self.assertRegex(response.content.decode(),r"<strong>[ABCD]</strong>")

    def test_reseed_preserves_visitor_items_with_matching_stems_and_titles(self):
        from .models import Assessment,AssessmentItem
        original=Question.objects.order_by('pk').first()
        copy=Question.objects.create(course=original.course,author=original.author,
            stem=original.stem,context='Rascunho criado por visitante',status='PENDING')
        base_exam=Assessment.objects.order_by('pk').first()
        visitor_exam=Assessment.objects.create(title=base_exam.title,
            term=base_exam.term,created_by=base_exam.created_by)
        before=(Question.objects.count(),Assessment.objects.count(),AssessmentItem.objects.count())
        call_command('seed_demo',verbosity=0)
        self.assertEqual((Question.objects.count(),Assessment.objects.count(),AssessmentItem.objects.count()),before)
        copy.refresh_from_db()
        self.assertEqual(copy.context,'Rascunho criado por visitante')
        self.assertFalse(AssessmentItem.objects.filter(assessment=visitor_exam).exists())
