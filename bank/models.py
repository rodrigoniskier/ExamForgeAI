from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

class AcademicTerm(models.Model):
    name=models.CharField(max_length=40,unique=True)
    active=models.BooleanField(default=True)
    class Meta: ordering=("-name",)
    def __str__(self): return self.name

class Course(models.Model):
    name=models.CharField(max_length=180)
    term=models.ForeignKey(AcademicTerm,on_delete=models.CASCADE,related_name="courses")
    target_count=models.PositiveIntegerField(default=5)
    class Meta:
        ordering=("name",)
        constraints=[models.UniqueConstraint(fields=("term","name"),name="unique_course_term")]
    def __str__(self): return f"{self.name} · {self.term}"

class Question(models.Model):
    class Status(models.TextChoices):
        PENDING="PENDING","Pendente"
        APPROVED="APPROVED","Aprovada"
        REJECTED="REJECTED","Rejeitada"
    class Type(models.TextChoices):
        SINGLE="SINGLE","Resposta única"
        MULTI="MULTI","Múltiplas afirmações"
        ASSERTION="ASSERTION","Asserção–razão"
    class Difficulty(models.TextChoices):
        EASY="EASY","Fácil"
        MEDIUM="MEDIUM","Média"
        HARD="HARD","Difícil"
    class Bloom(models.TextChoices):
        REMEMBER="REMEMBER","Lembrar"
        UNDERSTAND="UNDERSTAND","Compreender"
        APPLY="APPLY","Aplicar"
        ANALYZE="ANALYZE","Analisar"
        EVALUATE="EVALUATE","Avaliar"
        CREATE="CREATE","Criar"

    course=models.ForeignKey(Course,on_delete=models.CASCADE,related_name="questions")
    author=models.ForeignKey(User,on_delete=models.PROTECT,related_name="authored_questions")
    question_type=models.CharField(max_length=16,choices=Type.choices,default=Type.SINGLE)
    context=models.TextField(blank=True)
    stem=models.TextField()
    proposition_two=models.TextField(blank=True)
    rationale=models.TextField()
    bloom=models.CharField(max_length=20,choices=Bloom.choices,default=Bloom.APPLY)
    difficulty=models.CharField(max_length=12,choices=Difficulty.choices,default=Difficulty.MEDIUM)
    primary_area=models.CharField(max_length=120,blank=True)
    competency=models.CharField(max_length=240,blank=True)
    status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING)
    review_comment=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=("-created_at",)
    def __str__(self): return self.stem[:80]
    def clean(self):
        if self.question_type==self.Type.ASSERTION and not self.proposition_two.strip():
            raise ValidationError({"proposition_two":"Assertion–reason items require a second proposition."})

class Option(models.Model):
    question=models.ForeignKey(Question,on_delete=models.CASCADE,related_name="options")
    text=models.CharField(max_length=700)
    is_correct=models.BooleanField(default=False)
    order=models.PositiveSmallIntegerField(default=1)
    class Meta:
        ordering=("order","id")
        constraints=[models.UniqueConstraint(fields=("question","order"),name="unique_question_option_order")]
    def __str__(self): return self.text[:60]

class Assessment(models.Model):
    title=models.CharField(max_length=180)
    term=models.ForeignKey(AcademicTerm,on_delete=models.PROTECT)
    created_by=models.ForeignKey(User,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class AssessmentItem(models.Model):
    assessment=models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name="items")
    question=models.ForeignKey(Question,on_delete=models.PROTECT)
    order=models.PositiveIntegerField()
    class Meta:
        ordering=("order",)
        constraints=[models.UniqueConstraint(fields=("assessment","order"),name="unique_assessment_order"),models.UniqueConstraint(fields=("assessment","question"),name="unique_assessment_question")]
