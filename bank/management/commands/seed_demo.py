from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from bank.models import AcademicTerm,Course,Question,Option,Assessment,AssessmentItem
from bank.demo_content import COURSES,ITEMS

def oldest_or_create(model, *, defaults, **lookup):
    # Visitors may legitimately create another item with the same stem/title.
    # Keep the oldest seed record and leave every visitor-owned copy untouched.
    existing = model.objects.filter(**lookup).order_by('pk').first()
    if existing is not None:
        return existing, False
    return model.objects.create(**lookup, **defaults), True

class Command(BaseCommand):
    help='Create 32 original synthetic items and two assessments (idempotent).'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        if not settings.PORTFOLIO_DEMO: raise CommandError('PORTFOLIO_DEMO=1 is required.')
        editor,_=User.objects.get_or_create(username='editor.demo',defaults={'first_name':'Clara','last_name':'Mendes','email':'clara@example.invalid'})
        editor.is_staff=False;editor.is_superuser=False;editor.set_unusable_password();editor.save()
        term,_=AcademicTerm.objects.get_or_create(name='Ciclo 2026 · Formação profissional')
        for ci,(name,setting) in enumerate(COURSES):
            course,_=Course.objects.get_or_create(name=name,term=term,defaults={'target_count':8})
            for i,(scenario,stem,answers,rationale,bloom) in enumerate(ITEMS):
                q,created=oldest_or_create(Question,course=course,stem=stem,defaults={'author':editor,'context':f'Em uma organização fictícia, {setting}. {scenario}','rationale':rationale,'bloom':bloom,'difficulty':['EASY','MEDIUM','HARD'][i%3],'primary_area':name,'competency':['Interpretar informações de um processo','Planejar uma intervenção','Analisar evidências e comunicar decisões'][i%3],'status':'APPROVED' if i<6 else 'PENDING' if i==6 else 'REJECTED','review_comment':'Revisar o alinhamento ao nível cognitivo esperado.' if i==7 else ''})
                if created:
                    for pos in range(4):
                        source=(pos+ci+i)%4
                        Option.objects.create(question=q,text=answers[source],is_correct=source==0,order=pos+1)
            if ci<2:
                exam,_=oldest_or_create(Assessment,title=f'{name} · Avaliação formativa',defaults={'term':term,'created_by':editor})
                for pos,q in enumerate(course.questions.filter(status='APPROVED').order_by('id')[:5],1):
                    AssessmentItem.objects.get_or_create(assessment=exam,question=q,defaults={'order':pos})
        self.stdout.write(self.style.SUCCESS('32 items, 4 courses and 2 assessments ready.'))
