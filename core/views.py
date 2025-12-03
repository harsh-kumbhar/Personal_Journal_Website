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
