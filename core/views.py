# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date as _date
from .models import Quote, QuoteDisplayLog, JournalEntry, DailyMetrics, WorkoutSession, DietEntry, StudySession
from .forms import JournalEntryForm, QuickNoteForm, QuoteForm
from django.db.models import Sum

@login_required
def home_dashboard(request):
    # choose date param or default to today
    q_date = request.GET.get('date')
    if q_date:
        try:
            selected_date = timezone.datetime.strptime(q_date, '%Y-%m-%d').date()
        except Exception:
            selected_date = _date.today()
    else:
        selected_date = _date.today()

    user = request.user

    # Quote of the day - deterministic rotation by date + user id (if any)
    quote = None
    quote = Quote.objects.filter(approved=True).order_by('?').first()

    # Ensure QuoteDisplayLog recorded for this date (optional)
    try:
        qlog, created = QuoteDisplayLog.objects.get_or_create(date=selected_date, defaults={'quote': quote})
        if not created and qlog.quote != quote and quote is not None:
            # update if rotation changed (keeps one per day)
            qlog.quote = quote
            qlog.save()
    except Exception:
        # ignore logging issues in dev
        pass

    # Fetch entries for the selected date
    journal, _ = JournalEntry.objects.get_or_create(user=user, date=selected_date)
    daily_metrics = DailyMetrics.objects.filter(user=user, date=selected_date).first()

    workouts = WorkoutSession.objects.filter(user=user, date=selected_date).order_by('-start_time')
    diet_entries = DietEntry.objects.filter(user=user, date=selected_date).order_by('-time')
    studies = StudySession.objects.filter(user=user, date=selected_date)

    # Compute totals
    total_protein = 0.0
    for d in diet_entries:
        total_protein += d.total_protein() or 0.0

    context = {
        'selected_date': selected_date,
        'quote': quote,
        'journal': journal,
        'daily_metrics': daily_metrics,
        'workouts': workouts,
        'diet_entries': diet_entries,
        'studies': studies,
        'total_protein': round(total_protein, 2),
        'journal_form': JournalEntryForm(instance=journal),
        'quicknote_form': QuickNoteForm(),
        'quote_form': QuoteForm(),
    }

    # handle quick saves (journal or quicknote or quote)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_journal':
            form = JournalEntryForm(request.POST, instance=journal)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.user = user
                entry.save()
                form.save_m2m()
                return redirect('core:home')
        elif action == 'quick_note':
            qf = QuickNoteForm(request.POST)
            if qf.is_valid():
                note = qf.save(commit=False)
                note.user = user
                note.save()
                return redirect('core:home')
        elif action == 'add_quote':
            qf = QuoteForm(request.POST)
            if qf.is_valid():
                nq = qf.save(commit=False)
                nq.added_by = user
                nq.approved = True
                nq.save()
                return redirect('core:home')

    return render(request, 'core/home.html', context)


@login_required
def generate_daily_report(request, date=None):
    """
    Render a printable daily report for the given date (YYYY-MM-DD).
    If date is omitted, use today.
    """
    if isinstance(date, str) and date:
        try:
            selected_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        except Exception:
            selected_date = _date.today()
    else:
        selected_date = _date.today()

    user = request.user

    # gather same data as dashboard
    journal = JournalEntry.objects.filter(user=user, date=selected_date).first()
    daily_metrics = DailyMetrics.objects.filter(user=user, date=selected_date).first()
    workouts = WorkoutSession.objects.filter(user=user, date=selected_date)
    diet_entries = DietEntry.objects.filter(user=user, date=selected_date)
    studies = StudySession.objects.filter(user=user, date=selected_date)

    # Protein total
    total_protein = sum([d.total_protein() or 0.0 for d in diet_entries])

    context = {
        'selected_date': selected_date,
        'journal': journal,
        'daily_metrics': daily_metrics,
        'workouts': workouts,
        'diet_entries': diet_entries,
        'studies': studies,
        'total_protein': round(total_protein, 2),
        'generated_at': timezone.now(),
        'user': user,
    }

    return render(request, 'core/daily_report.html', context)


# core/views.py (append / merge)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date as _date
from .models import DailyMetrics, WaterLog, Habit, HabitLog, BadHabit, BadHabitLog
from .forms import DailyMetricsForm, HabitForm, HabitLogForm, BadHabitForm, BadHabitLogForm
from django.db.models import Avg, Sum, Count
from django.contrib import messages

@login_required
def entries_view(request):
    user = request.user
    q_date = request.GET.get('date')
    try:
        selected_date = timezone.datetime.strptime(q_date, '%Y-%m-%d').date() if q_date else _date.today()
    except Exception:
        selected_date = _date.today()

    # Ensure DailyMetrics exists for the date
    daily_metrics, _ = DailyMetrics.objects.get_or_create(user=user, date=selected_date)

    # forms (keep DM and habit forms for editor use)
    dm_form = DailyMetricsForm(instance=daily_metrics)
    habit_form = HabitForm()
    habitlog_form = HabitLogForm(initial={'date': selected_date})
    badhabit_form = BadHabitForm()
    badhabitlog_form = BadHabitLogForm(initial={'date': selected_date})

    if request.method == 'POST':
        action = request.POST.get('action')
        # Save daily metrics
        if action == 'save_metrics':
            dm_form = DailyMetricsForm(request.POST, instance=daily_metrics)
            if dm_form.is_valid():
                obj = dm_form.save(commit=False)
                obj.user = user
                obj.save()
                messages.success(request, "Daily metrics saved.")
                return redirect(f"{request.path}?date={obj.date.isoformat()}")
            else:
                messages.error(request, "Please fix errors in metrics form.")

        # Add a good habit (simple input: name)
        elif action == 'add_habit':
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, "Please enter a habit name.")
            else:
                # avoid duplicates per user
                bh, created = Habit.objects.get_or_create(user=user, name=name)
                if created:
                    messages.success(request, f"Habit '{name}' created.")
                else:
                    messages.info(request, f"Habit '{name}' already exists.")
                return redirect(request.path)

        # Mark good habit done (expects hidden habit id and optional date)
        elif action == 'mark_habit':
            habit_id = request.POST.get('habit') or request.POST.get('habit_id')
            date_str = request.POST.get('date')
            try:
                if date_str:
                    log_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    log_date = selected_date
            except Exception:
                log_date = selected_date

            if not habit_id:
                messages.error(request, "No habit specified.")
            else:
                try:
                    hobj = Habit.objects.get(id=int(habit_id), user=user)
                except (Habit.DoesNotExist, ValueError):
                    messages.error(request, "Invalid habit.")
                    return redirect(request.path)

                # create HabitLog (avoid duplicate for same date)
                hl, created = HabitLog.objects.get_or_create(habit=hobj, date=log_date, defaults={'notes': ''})
                if created:
                    update_habit_streak(hobj, log_date)
                    messages.success(request, f"Marked '{hobj.name}' done for {log_date}.")
                else:
                    messages.info(request, f"'{hobj.name}' was already marked for {log_date}.")
                return redirect(f"{request.path}?date={log_date.isoformat()}")

        # Add a bad habit (simple input: name)
        elif action == 'add_bad_habit':
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, "Please enter a bad habit name.")
            else:
                bh, created = BadHabit.objects.get_or_create(user=user, name=name)
                if created:
                    messages.success(request, f"Bad habit '{name}' added.")
                else:
                    messages.info(request, f"Bad habit '{name}' already exists.")
                return redirect(request.path)

        # Mark bad habit (log a slip-up). Accepts 'habit' or 'habit_id', 'date' optional, 'notes' optional.
        elif action == 'mark_bad_habit':
            habit_id = request.POST.get('habit') or request.POST.get('habit_id')
            notes = request.POST.get('notes', '').strip()
            date_str = request.POST.get('date')
            try:
                if date_str:
                    log_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    log_date = selected_date
            except Exception:
                log_date = selected_date

            if not habit_id:
                messages.error(request, "No bad habit specified.")
            else:
                try:
                    bh_obj = BadHabit.objects.get(id=int(habit_id), user=user)
                except (BadHabit.DoesNotExist, ValueError):
                    messages.error(request, "Invalid bad habit.")
                    return redirect(request.path)

                bhl, created = BadHabitLog.objects.get_or_create(habit=bh_obj, date=log_date, defaults={'notes': notes})
                if created:
                    # if notes provided and model supports it, save (get_or_create set notes in defaults)
                    messages.success(request, f"Logged bad habit '{bh_obj.name}' for {log_date}.")
                else:
                    # if already exists but notes provided and empty, update
                    if notes and not bhl.notes:
                        bhl.notes = notes
                        bhl.save()
                        messages.success(request, "Slip-up updated with notes.")
                    else:
                        messages.info(request, f"'{bh_obj.name}' already logged for {log_date}.")
                return redirect(f"{request.path}?date={log_date.isoformat()}")

    # Summary data (last 7 days)
    from datetime import timedelta
    start_7 = selected_date - timedelta(days=6)
    metrics_7 = DailyMetrics.objects.filter(user=user, date__range=(start_7, selected_date)).order_by('-date')
    avg_water = metrics_7.aggregate(avg_water=Avg('water_ml'))['avg_water'] or 0
    avg_screen = metrics_7.aggregate(avg_screen=Avg('screen_time_minutes'))['avg_screen'] or 0
    avg_sleep = metrics_7.aggregate(avg_sleep=Avg('sleep_hours'))['avg_sleep'] or 0

    # habits & bad habits
    habits = Habit.objects.filter(user=user).order_by('-created_at')
    bad_habits = BadHabit.objects.filter(user=user).order_by('-created_at')
    today_habit_logs = HabitLog.objects.filter(habit__user=user, date=selected_date)
    today_bad_logs = BadHabitLog.objects.filter(habit__user=user, date=selected_date)

    # new context helpers
    completed_habit_ids = list(today_habit_logs.values_list('habit_id', flat=True))
    selected_date_iso = selected_date.isoformat()

    context = {
        'selected_date': selected_date,
        'selected_date_iso': selected_date_iso,
        'dm_form': dm_form,
        'habit_form': habit_form,
        'habitlog_form': habitlog_form,
        'badhabit_form': badhabit_form,
        'badhabitlog_form': badhabitlog_form,
        'metrics_7': metrics_7,
        'avg_water': int(avg_water),
        'avg_screen': int(avg_screen),
        'avg_sleep': round(avg_sleep, 1) if avg_sleep else None,
        'habits': habits,
        'bad_habits': bad_habits,
        'today_habit_logs': today_habit_logs,
        'today_bad_logs': today_bad_logs,
        'completed_habit_ids': completed_habit_ids,
    }

    return render(request, 'core/entries.html', context)
def update_habit_streak(habit, done_date):
    """
    Basic streak updater used when a habit is marked done for a date.
    Rules:
      - If last_done_date == done_date: do nothing (already logged).
      - If last_done_date == done_date - 1 day: increment current_streak.
      - Otherwise reset current_streak to 1.
      - Update best_streak if current_streak exceeds it.
    """
    try:
        from datetime import timedelta
        # handle None defaults safely
        last = habit.last_done_date
        if last == done_date:
            return  # already counted for this date

        if last:
            yesterday = done_date - timedelta(days=1)
            if last == yesterday:
                habit.current_streak = (habit.current_streak or 0) + 1
            else:
                habit.current_streak = 1
        else:
            habit.current_streak = 1

        habit.last_done_date = done_date
        if (habit.current_streak or 0) > (habit.best_streak or 0):
            habit.best_streak = habit.current_streak

        habit.save(update_fields=['current_streak', 'best_streak', 'last_done_date'])
    except Exception as e:
        # don't crash the whole view for a streak calculation error — log to console for now
        import logging
        logging.exception("Failed to update habit streak: %s", e)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from .models import WorkoutSession, Exercise
from .forms import WorkoutSessionForm, WorkoutExerciseFormSet

@login_required
def workout_list(request):
    sessions = WorkoutSession.objects.filter(user=request.user).order_by('-date')
    return render(request, 'core/workout_list.html', {'sessions': sessions})

@login_required
def workout_detail(request, pk):
    session = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    return render(request, 'core/workout_detail.html', {'session': session})

@login_required
def workout_create(request):
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        formset = WorkoutExerciseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                workout = form.save(commit=False)
                workout.user = request.user
                workout.save()
                
                exercises = formset.save(commit=False)
                for exercise in exercises:
                    exercise.workout = workout
                    exercise.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                return redirect('core:workout_detail', pk=workout.pk)
    else:
        form = WorkoutSessionForm(initial={'date': timezone.now().date()})
        formset = WorkoutExerciseFormSet()

    all_exercises = Exercise.objects.values_list('name', flat=True).order_by('name')
    return render(request, 'core/workout_form.html', {
        'form': form, 'formset': formset, 'all_exercises': all_exercises, 'title': 'Record Workout'
    })

@login_required
def workout_update(request, pk):
    workout = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST, instance=workout)
        formset = WorkoutExerciseFormSet(request.POST, instance=workout)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                exercises = formset.save(commit=False)
                for exercise in exercises:
                    exercise.workout = workout
                    exercise.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                return redirect('core:workout_detail', pk=workout.pk)
    else:
        form = WorkoutSessionForm(instance=workout)
        formset = WorkoutExerciseFormSet(instance=workout)

    all_exercises = Exercise.objects.values_list('name', flat=True).order_by('name')
    return render(request, 'core/workout_form.html', {
        'form': form, 'formset': formset, 'all_exercises': all_exercises, 'title': 'Edit Workout'
    })

@login_required
def workout_delete(request, pk):
    workout = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    if request.method == 'POST':
        workout.delete()
        return redirect('core:workout_list')
    return render(request, 'core/workout_confirm_delete.html', {'object': workout})


# core/views.py
# ... keep existing imports ...
from .models import FoodItem, DietEntry, DietItem
from .forms import FoodItemForm, DietEntryForm, DietItemFormSet

# --- FOOD LIBRARY VIEWS ---
@login_required
def food_library(request):
    """ List all foods and allow adding new ones """
    foods = FoodItem.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food = form.save(commit=False)
            food.created_by = request.user
            food.save()
            return redirect('core:food_library')
    else:
        form = FoodItemForm()
        
    return render(request, 'core/food_library.html', {'foods': foods, 'form': form})

# --- MEAL LOGGING VIEWS ---
@login_required
def diet_list(request):
    """ Show history of meals """
    entries = DietEntry.objects.filter(user=request.user).order_by('-date', '-time')
    return render(request, 'core/diet_list.html', {'entries': entries})

@login_required
def diet_create(request):
    """ Log a new meal """
    if request.method == 'POST':
        form = DietEntryForm(request.POST)
        formset = DietItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                entry = form.save(commit=False)
                entry.user = request.user
                entry.save()
                
                items = formset.save(commit=False)
                for item in items:
                    item.diet_entry = entry
                    item.save() # Macros are auto-calculated in the model's save() method
                
                for obj in formset.deleted_objects:
                    obj.delete()
                    
                return redirect('core:diet_list')
    else:
        form = DietEntryForm(initial={'date': timezone.now().date(), 'time': timezone.now().time()})
        formset = DietItemFormSet()

    # Pass food names for the datalist
    all_foods = FoodItem.objects.values_list('name', flat=True).order_by('name')
    
    return render(request, 'core/diet_form.html', {
        'form': form, 
        'formset': formset, 
        'all_foods': all_foods,
        'title': 'Log Meal'
    })

@login_required
def diet_detail(request, pk):
    entry = get_object_or_404(DietEntry, pk=pk, user=request.user)
    return render(request, 'core/diet_detail.html', {'entry': entry})

@login_required
def diet_delete(request, pk):
    entry = get_object_or_404(DietEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        return redirect('core:diet_list')
    return render(request, 'core/diet_confirm_delete.html', {'object': entry})


# ... existing imports ...
from .models import StudySession, Course, Project, InternshipLog
from .forms import StudySessionForm, CourseForm, ProjectForm, InternshipLogForm

# --- ACADEMICS VIEWS ---

@login_required
def academics_dashboard(request):
    """ Main Hub for Academics & Internship """
    # Get recent data
    recent_sessions = StudySession.objects.filter(user=request.user).order_by('-date', '-start_time')[:5]
    active_projects = Project.objects.filter(user=request.user, status='active')
    active_courses = Course.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_internship = InternshipLog.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Calculate simple stats (Python side to avoid template math)
    total_internship_hours = sum(log.hours for log in InternshipLog.objects.filter(user=request.user))
    total_study_hours = sum((s.duration_hours or 0) for s in StudySession.objects.filter(user=request.user))
    
    return render(request, 'core/academics_dashboard.html', {
        'recent_sessions': recent_sessions,
        'active_projects': active_projects,
        'active_courses': active_courses,
        'recent_internship': recent_internship,
        'total_internship_hours': round(total_internship_hours, 1),
        'total_study_hours': round(total_study_hours, 1),
    })

@login_required
def study_session_create(request):
    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            # If M2M topics were used in form, we'd need form.save_m2m()
            return redirect('core:academics_dashboard')
    else:
        form = StudySessionForm(initial={'date': timezone.now().date(), 'start_time': timezone.now().time()})
    
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Log Study Session', 'btn_text': 'Start Session'
    })

@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            return redirect('core:academics_dashboard')
    else:
        form = CourseForm()
    
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Add New Course', 'btn_text': 'Save Course'
    })

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('core:academics_dashboard')
    else:
        form = ProjectForm()
    
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Start New Project', 'btn_text': 'Create Project'
    })

@login_required
def internship_log_create(request):
    if request.method == 'POST':
        form = InternshipLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            return redirect('core:academics_dashboard')
    else:
        form = InternshipLogForm(initial={'date': timezone.now().date()})
    
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Log Internship Hours', 'btn_text': 'Log Work'
    })


# core/views.py

# ... existing imports ...
from django.urls import reverse

# --- ACADEMICS: UPDATE & DELETE VIEWS ---

# 1. STUDY SESSION
@login_required
def study_session_update(request, pk):
    obj = get_object_or_404(StudySession, pk=pk, user=request.user)
    if request.method == 'POST':
        form = StudySessionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('core:academics_dashboard')
    else:
        form = StudySessionForm(instance=obj)
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Edit Study Session', 'btn_text': 'Update'
    })

@login_required
def study_session_delete(request, pk):
    obj = get_object_or_404(StudySession, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('core:academics_dashboard')
    return render(request, 'core/generic_confirm_delete.html', {
        'object': obj, 'type_name': 'Study Session'
    })

# 2. COURSE
@login_required
def course_update(request, pk):
    obj = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('core:academics_dashboard')
    else:
        form = CourseForm(instance=obj)
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Edit Course', 'btn_text': 'Update'
    })

@login_required
def course_delete(request, pk):
    obj = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('core:academics_dashboard')
    return render(request, 'core/generic_confirm_delete.html', {
        'object': obj, 'type_name': f"Course: {obj.title}"
    })

# 3. PROJECT
@login_required
def project_update(request, pk):
    obj = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('core:academics_dashboard')
    else:
        form = ProjectForm(instance=obj)
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Edit Project', 'btn_text': 'Update'
    })

@login_required
def project_delete(request, pk):
    obj = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('core:academics_dashboard')
    return render(request, 'core/generic_confirm_delete.html', {
        'object': obj, 'type_name': f"Project: {obj.title}"
    })

# 4. INTERNSHIP LOG
@login_required
def internship_log_update(request, pk):
    obj = get_object_or_404(InternshipLog, pk=pk, user=request.user)
    if request.method == 'POST':
        form = InternshipLogForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('core:academics_dashboard')
    else:
        form = InternshipLogForm(instance=obj)
    return render(request, 'core/generic_form.html', {
        'form': form, 'title': 'Edit Work Log', 'btn_text': 'Update'
    })

@login_required
def internship_log_delete(request, pk):
    obj = get_object_or_404(InternshipLog, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('core:academics_dashboard')
    return render(request, 'core/generic_confirm_delete.html', {
        'object': obj, 'type_name': 'Internship Log'
    })

# core/views.py
from django.http import JsonResponse
from .models import Exercise, WorkoutType

# ... existing views ...

@login_required
def get_exercises_by_type(request):
    """
    API endpoint: Returns a list of exercises based on the selected WorkoutType ID.
    Logic: Type -> Targeted Muscles -> Exercises with those primary muscles.
    """
    type_id = request.GET.get('type_id')
    
    if type_id:
        try:
            workout_type = WorkoutType.objects.get(pk=type_id)
            # 1. Get all muscles linked to this workout type
            target_muscles = workout_type.targeted_muscles.all()
            
            if target_muscles.exists():
                # 2. Filter exercises that hit these muscles
                exercises = Exercise.objects.filter(primary_muscle__in=target_muscles).order_by('name')
            else:
                # If no muscles linked (e.g. "General"), show ALL exercises
                exercises = Exercise.objects.all().order_by('name')
                
        except WorkoutType.DoesNotExist:
            exercises = Exercise.objects.none()
    else:
        # No type selected? Return all or none. Let's return all for flexibility.
        exercises = Exercise.objects.all().order_by('name')
    
    # Return as JSON list for the frontend
    data = list(exercises.values('name'))
    return JsonResponse({'exercises': data})