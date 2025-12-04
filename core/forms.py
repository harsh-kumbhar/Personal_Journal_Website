# core/forms.py
from django import forms
from django.forms import DateInput, TimeInput

from .models import (
    JournalEntry, QuickNote, Quote,
    DailyMetrics, Habit, HabitLog,
    BadHabit, BadHabitLog
)


# --------------------------
# JOURNAL / QUOTE / NOTES
# --------------------------

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = [
            'date', 'moment_of_day', 'grateful_for', 'regret',
            'highlights', 'quote_added', 'mood'
        ]
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
            'moment_of_day': forms.Textarea(attrs={'rows': 2}),
            'grateful_for': forms.Textarea(attrs={'rows': 2}),
            'regret': forms.Textarea(attrs={'rows': 2}),
            'highlights': forms.Textarea(attrs={'rows': 2}),
        }


class QuickNoteForm(forms.ModelForm):
    class Meta:
        model = QuickNote
        fields = ['content', 'category']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Quick idea / todo...'})
        }


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['text', 'author']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a quote...'}),
            'author': forms.TextInput(attrs={'placeholder': 'Author (optional)'})
        }


# --------------------------
# DAILY METRICS (NO WATER FORM)
# --------------------------

class DailyMetricsForm(forms.ModelForm):
    class Meta:
        model = DailyMetrics
        fields = [
            'date', 'water_ml', 'sleep_hours',
            'screen_time_minutes', 'steps', 'books_minutes',
            'notes'
        ]
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


# --------------------------
# HABITS
# --------------------------

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'goal_frequency', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Habit name', 'required': True}),
        }


class HabitLogForm(forms.ModelForm):
    class Meta:
        model = HabitLog
        fields = ['habit', 'date', 'notes']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


# --------------------------
# BAD HABITS
# --------------------------

class BadHabitForm(forms.ModelForm):
    class Meta:
        model = BadHabit
        fields = ['name', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Bad habit name e.g. Overthinking', 'required': True}),
        }


class BadHabitLogForm(forms.ModelForm):
    class Meta:
        model = BadHabitLog
        fields = ['habit', 'date', 'notes']
    widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }
