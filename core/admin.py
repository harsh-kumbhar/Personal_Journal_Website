# core/admin.py
from django.contrib import admin
from . import models

# Simple registers
admin.site.register(models.Tag)
admin.site.register(models.Attachment)
admin.site.register(models.Muscle)
admin.site.register(models.WorkoutType)
admin.site.register(models.Exercise)
admin.site.register(models.FoodItem)
admin.site.register(models.Quote)
admin.site.register(models.Topic)

# Workout inlines
class WorkoutExerciseInline(admin.TabularInline):
    model = models.WorkoutExercise
    extra = 1
    readonly_fields = ()
    fields = ('order','exercise','sets','reps','weight_kg','rest_seconds','notes')

@admin.register(models.WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('user','date','workout_type','duration_minutes')
    list_filter = ('workout_type','date','user')
    search_fields = ('notes',)
    inlines = [WorkoutExerciseInline]
    date_hierarchy = 'date'

# PRRecord
@admin.register(models.PRRecord)
class PRRecordAdmin(admin.ModelAdmin):
    list_display = ('user','exercise','max_weight_kg','reps_at_max','date')
    search_fields = ('exercise__name','user__username')
    list_filter = ('date',)

# Diet admin with inline items
class DietItemInline(admin.TabularInline):
    model = models.DietItem
    extra = 1
    fields = ('food','amount','unit','protein_calculated','calories_calculated')
    readonly_fields = ('protein_calculated','calories_calculated')

@admin.register(models.DietEntry)
class DietEntryAdmin(admin.ModelAdmin):
    list_display = ('user','date','meal_type','time')
    list_filter = ('meal_type','date','user')
    inlines = [DietItemInline]
    search_fields = ('notes',)

@admin.register(models.NutritionGoal)
class NutritionGoalAdmin(admin.ModelAdmin):
    list_display = ('user','daily_protein','daily_calories')

class MealTemplateItemInline(admin.TabularInline):
    model = models.MealTemplateItem
    extra = 1
    fields = ('food', 'amount', 'order')
    readonly_fields = ()

@admin.register(models.MealTemplate)
class MealTemplateAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    inlines = [MealTemplateItemInline]
    search_fields = ('name', 'user__username')

# Academics
@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('user','title','provider','hours_estimated')
    search_fields = ('title','provider')

@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user','title','status','start_date','end_date')
    search_fields = ('title','tech_stack')

class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user','date','activity_type','duration_hours')
    list_filter = ('activity_type','date','user')

admin.site.register(models.StudySession, StudySessionAdmin)
admin.site.register(models.InternshipLog)

# General metrics & habits
@admin.register(models.DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    list_display = ('user','date','water_ml','sleep_hours','screen_time_minutes')
    search_fields = ('bad_habits','notes')

class HabitLogInline(admin.TabularInline):
    model = models.HabitLog
    extra = 0

@admin.register(models.Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('user','name','goal_frequency','current_streak','active')
    inlines = [HabitLogInline]

admin.site.register(models.WaterLog)
admin.site.register(models.QuoteDisplayLog)
admin.site.register(models.JournalEntry)
admin.site.register(models.QuickNote)
admin.site.register(models.DailyReport)
admin.site.register(models.ExportJob)
admin.site.register(models.BackupSnapshot)
admin.site.register(models.Notification)
admin.site.register(models.UserSettings)
admin.site.register(models.WeeklySummary)
admin.site.register(models.ExerciseProgress)



from .models import BadHabit # <--- Make sure it is imported


@admin.register(BadHabit)
class BadHabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'active')
    list_filter = ('active', 'user')