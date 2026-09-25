from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Assessment,Option,Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model=Question
        fields=["course","question_type","context","stem","proposition_two","rationale","bloom","difficulty","primary_area","competency","status","review_comment"]
        labels={"course":"Componente", "question_type":"Tipo de questão", "context":"Contexto", "stem":"Enunciado", "proposition_two":"Segunda proposição", "rationale":"Justificativa", "bloom":"Taxonomia de Bloom", "difficulty":"Dificuldade", "primary_area":"Área", "competency":"Competência", "status":"Decisão humana", "review_comment":"Comentário de revisão"}
        widgets={"context":forms.Textarea(attrs={"rows":4}),"stem":forms.Textarea(attrs={"rows":3}),"proposition_two":forms.Textarea(attrs={"rows":2}),"rationale":forms.Textarea(attrs={"rows":5}),"review_comment":forms.Textarea(attrs={"rows":3})}

class ValidatedOptions(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        rows=[f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if len(rows)<2: raise forms.ValidationError("Informe pelo menos duas alternativas.")
        correct=sum(bool(r.get("is_correct")) for r in rows)
        if self.instance.question_type in ("SINGLE","ASSERTION") and correct != 1:
            raise forms.ValidationError("Este tipo de item exige exatamente uma alternativa correta.")
        if self.instance.question_type == "MULTI" and correct < 1:
            raise forms.ValidationError("Marque pelo menos uma alternativa correta.")

OptionFormSet=inlineformset_factory(Question,Option,formset=ValidatedOptions,fields=("text","is_correct","order"),extra=2,min_num=2,validate_min=True,can_delete=True)

class AssessmentForm(forms.ModelForm):
    course=forms.ModelChoiceField(queryset=None,label="Componente")
    count=forms.IntegerField(label="Quantidade de questões",min_value=1,max_value=100,initial=5)
    class Meta:
        model=Assessment
        fields=["title","term"]
        labels={"title":"Título da avaliação", "term":"Período"}
    def __init__(self,*args,**kwargs):
        from .models import Course
        super().__init__(*args,**kwargs)
        self.fields["course"].queryset=Course.objects.select_related("term").all()
