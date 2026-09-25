from django.contrib import admin
from .models import AcademicTerm,Assessment,AssessmentItem,Course,Option,Question
class OptionInline(admin.TabularInline):
    model=Option; extra=0
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display=("id","course","question_type","bloom","difficulty","status","author")
    list_filter=("status","question_type","bloom","difficulty","course")
    search_fields=("stem","context","rationale")
    inlines=[OptionInline]
admin.site.register(AcademicTerm); admin.site.register(Course); admin.site.register(Assessment); admin.site.register(AssessmentItem)
admin.site.site_header="ExamForge AI Administration"; admin.site.site_title="ExamForge AI"
