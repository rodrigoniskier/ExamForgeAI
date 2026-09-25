from django import forms
from django.forms import inlineformset_factory
from .models import Assessment,Option,Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model=Question
        fields=["course","question_type","context","stem","proposition_two","rationale","bloom","difficulty","primary_area","competency","status","review_comment"]
        widgets={"context":forms.Textarea(attrs={"rows":4}),"stem":forms.Textarea(attrs={"rows":3}),"proposition_two":forms.Textarea(attrs={"rows":2}),"rationale":forms.Textarea(attrs={"rows":5}),"review_comment":forms.Textarea(attrs={"rows":3})}

OptionFormSet=inlineformset_factory(Question,Option,fields=("text","is_correct","order"),extra=4,min_num=2,validate_min=True,can_delete=True)

class AssessmentForm(forms.ModelForm):
    course=forms.ModelChoiceField(queryset=None)
    count=forms.IntegerField(min_value=1,max_value=100,initial=10)
    class Meta:
        model=Assessment
        fields=["title","term"]
    def __init__(self,*args,**kwargs):
        from .models import Course
        super().__init__(*args,**kwargs)
        self.fields["course"].queryset=Course.objects.select_related("term").all()
