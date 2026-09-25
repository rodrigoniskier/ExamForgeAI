import json,random,re
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseForbidden
from django.db.models import Q
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
    qs=Question.objects.select_related("course","author")
    query=request.GET.get("q","").strip()
    if query: qs=qs.filter(Q(stem__icontains=query)|Q(context__icontains=query))
    for key in ("status","bloom","difficulty"):
        if request.GET.get(key): qs=qs.filter(**{key:request.GET[key]})
    if request.GET.get("course","").isdigit(): qs=qs.filter(course_id=request.GET["course"])
    return render(request,"dashboard.html",{"questions":qs[:80],"counts":{"total":Question.objects.count(),"approved":Question.objects.filter(status="APPROVED").count(),"pending":Question.objects.filter(status="PENDING").count(),"courses":Course.objects.count()},"courses":Course.objects.all(),"statuses":Question.Status.choices,"blooms":Question.Bloom.choices,"difficulties":Question.Difficulty.choices,"assessments":Assessment.objects.order_by("-created_at")[:8]})

@login_required
@transaction.atomic
def question_create(request, pk=None):
    question=get_object_or_404(Question,pk=pk,author=request.user) if pk else Question(author=request.user)
    if settings.PORTFOLIO_DEMO and pk:
        # The shared seed remains intact: editing creates a new pending copy.
        if question.pk not in request.session.get("owned_questions",[]):
            from .models import Option
            original=question
            question=Question(author=request.user)
            initial={f:getattr(original,f) for f in QuestionForm.Meta.fields}
            initial["status"]="PENDING"
        else: initial=None
    else: initial=None
    form=QuestionForm(request.POST or None,instance=question,initial=initial)
    formset=OptionFormSet(request.POST or None,instance=question,prefix="options",initial=[{"text":o.text,"is_correct":o.is_correct,"order":o.order} for o in original.options.all()] if initial and request.method=="GET" else None)
    if request.method=="POST" and form.is_valid() and formset.is_valid():
        if settings.PORTFOLIO_DEMO and Question.objects.count() >= 150:
            return HttpResponseForbidden("Limite de itens da demonstração atingido.")
        question=form.save(commit=False); question.author=request.user; question.full_clean(); question.save()
        options=formset.save(commit=False)
        for deleted in formset.deleted_objects: deleted.delete()
        for option in options: option.question=question; option.save()
        if question.question_type==Question.Type.SINGLE and question.options.filter(is_correct=True).count()!=1:
            transaction.set_rollback(True); messages.error(request,"Single-answer items require exactly one correct option.")
        else:
            owned=request.session.get("owned_questions",[])
            if question.pk not in owned: request.session["owned_questions"]=owned+[question.pk]
            messages.success(request,"Questão salva. A aprovação permanece uma decisão humana."); return redirect("question_detail",pk=question.pk)
    return render(request,"question_form.html",{"form":form,"formset":formset,"editing":bool(pk)})

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
        if course.term_id != form.cleaned_data["term"].pk:
            form.add_error("term","O período precisa corresponder ao componente escolhido.")
            return render(request,"assessment_form.html",{"form":form})
        if settings.PORTFOLIO_DEMO and Assessment.objects.count() >= 40:
            return HttpResponseForbidden("Limite de avaliações da demonstração atingido.")
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
    answer_key=[]
    for item in assessment.items.all():
        letters=[chr(65+i) for i,o in enumerate(item.question.options.all()) if o.is_correct]
        answer_key.append({"number":item.order,"answer":", ".join(letters)})
    return render(request,"assessment_detail.html",{"assessment":assessment,"answer_key":answer_key})

@login_required
def blackboard_export(request,pk):
    assessment=get_object_or_404(Assessment.objects.prefetch_related("items__question__options"),pk=pk)
    lines=[]
    for item in assessment.items.all():
        q=item.question
        header=re.sub(r"[\r\n\t]+"," ",f"{q.context} {q.stem}".strip())
        parts=["MA" if q.options.filter(is_correct=True).count()>1 else "MC",header]
        for option in q.options.all():
            text=re.sub(r"[\r\n\t]+"," ",option.text.strip())
            parts.extend([text,"correct" if option.is_correct else "incorrect"])
        lines.append("\t".join(parts))
    response=HttpResponse("\n".join(lines),content_type="text/plain; charset=utf-8")
    response["Content-Disposition"]=f'attachment; filename="examforge_{assessment.pk}.txt"'
    return response

@require_POST
@login_required
def logout_view(request):
    logout(request); return redirect("login")
