from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from bank.models import AcademicTerm,Course,Option,Question
class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        admin,_=User.objects.get_or_create(username="admin",defaults={"is_staff":True,"is_superuser":True,"email":"admin@example.com"}); admin.set_password("Demo-Admin-12345"); admin.save()
        editor,_=User.objects.get_or_create(username="editor.demo",defaults={"first_name":"Demo","last_name":"Editor","email":"editor@example.com"}); editor.set_password("Demo-Editor-12345"); editor.save()
        term,_=AcademicTerm.objects.get_or_create(name="Demo 2026")
        course,_=Course.objects.get_or_create(term=term,name="Applied Health Sciences",defaults={"target_count":5})
        if not Question.objects.exists():
            for i in range(8):
                q=Question.objects.create(course=course,author=editor,context=f"Synthetic case scenario {i+1}.",stem=f"Which action is most appropriate in demo case {i+1}?",rationale="Synthetic rationale for portfolio demonstration.",bloom=["APPLY","ANALYZE"][i%2],difficulty=["EASY","MEDIUM","HARD"][i%3],primary_area="Demo domain",competency="Apply information to a structured scenario",status="APPROVED" if i<6 else "PENDING")
                for n,text in enumerate(["Best option","Plausible distractor 1","Plausible distractor 2","Plausible distractor 3"],1): Option.objects.create(question=q,text=f"{text} for item {i+1}",is_correct=n==1,order=n)
        self.stdout.write(self.style.SUCCESS("Synthetic ExamForge AI data ready."))
