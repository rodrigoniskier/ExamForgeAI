import json,random,re
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_POST
from .ai import generate_question,review_question
from .forms import AssessmentForm,OptionFormSet,QuestionForm
from .models import AcademicTerm,Assessment,AssessmentItem,Course,Question

class ExamForgeLoginView(LoginView):
    template_name="login.html"
    redirect_authenticated_user=True

@login_required
def dashboard(request):
    questions=Question.objects.select_related("course","author")[:50]
    return render(request,"dashboard.html",{"questions":questions,"counts":{"total":Question.objects.count(),"approved":Question.objects.filter(status="APPROVED").count(),"pending":Question.objects.filter(status="PENDING").count()},"assessments":Assessment.objects.order_by("-created_at")[:8]})

@login_required
@transaction.atomic
def question_create(request):
    question=Question(author=request.user)
    form=QuestionForm(request.POST or None,instance=question)
    formset=OptionFormSet(request.POST or None,instance=question,prefix="options")
    if request.method=="POST" and form.is_valid() and formset.is_valid():
        question=form.save(commit=False); question.author=request.user; question.full_clean(); question.save()
        options=formset.save(commit=False)
        for deleted in formset.deleted_objects: deleted.delete()
        for option in options: option.question=question; option.save()
        if question.question_type==Question.Type.SINGLE and question.options.filter(is_correct=True).count()!=1:
            transaction.set_rollback(True); messages.error(request,"Single-answer items require exactly one correct option.")
        else:
            messages.success(request,"Question saved."); return redirect("dashboard")
    return render(request,"question_form.html",{"form":form,"formset":formset})

@login_required
def question_detail(request,pk):
    q=get_object_or_404(Question.objects.select_related("course","author").prefetch_related("options"),pk=pk)
    return render(request,"question_detail.html",{"q":q})

@require_POST
@login_required
def ai_generate(request):
    try:
        data=json.loads(request.body)
        course=get_object_or_404(Course,pk=data.get("course_id"))
        draft=generate_question(data.get("prompt",""),course.name,{"bloom":data.get("bloom"),"difficulty":data.get("difficulty"),"primary_area":data.get("primary_area"),"competency":data.get("competency")})
        return JsonResponse(draft)
    except (ValueError,KeyError,json.JSONDecodeError) as exc:
        return JsonResponse({"error":str(exc)},status=400)
    except RuntimeError as exc:
        return JsonResponse({"error":str(exc)},status=503)
    except Exception:
        return JsonResponse({"error":"AI generation failed."},status=502)

@require_POST
@login_required
def ai_review(request,pk):
    q=get_object_or_404(Question.objects.prefetch_related("options"),pk=pk)
    try: report=review_question(q)
    except RuntimeError as exc: return JsonResponse({"error":str(exc)},status=503)
    except Exception: return JsonResponse({"error":"AI review failed."},status=502)
    return JsonResponse({"report":report})

@login_required
@transaction.atomic
def assessment_create(request):
    form=AssessmentForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        course=form.cleaned_data["course"]; count=form.cleaned_data["count"]
        pool=list(Question.objects.filter(course=course,status=Question.Status.APPROVED).prefetch_related("options"))
        if len(pool)<count:
            messages.error(request,f"Only {len(pool)} approved items are available for this course.")
        else:
            assessment=form.save(commit=False); assessment.created_by=request.user; assessment.save()
            selected=random.sample(pool,count)
            AssessmentItem.objects.bulk_create([AssessmentItem(assessment=assessment,question=q,order=i+1) for i,q in enumerate(selected)])
            return redirect("assessment_detail",pk=assessment.pk)
    return render(request,"assessment_form.html",{"form":form})

@login_required
def assessment_detail(request,pk):
    assessment=get_object_or_404(Assessment.objects.prefetch_related("items__question__options"),pk=pk)
    return render(request,"assessment_detail.html",{"assessment":assessment})

@login_required
def blackboard_export(request,pk):
    assessment=get_object_or_404(Assessment.objects.prefetch_related("items__question__options"),pk=pk)
    lines=[]
    for item in assessment.items.all():
        q=item.question
        header=re.sub(r"[\r\n\t]+"," ",f"{q.context} {q.stem}".strip())
        parts=["MC",header]
        for option in q.options.all():
            text=re.sub(r"[\r\n\t]+"," ",option.text.strip())
            parts.extend([text,"correct" if option.is_correct else "incorrect"])
        lines.append("\t".join(parts))
    response=HttpResponse("\n\n".join(lines),content_type="text/plain; charset=utf-8")
    response["Content-Disposition"]=f'attachment; filename="examforge_{assessment.pk}.txt"'
    return response

@require_POST
@login_required
def logout_view(request):
    logout(request); return redirect("login")
