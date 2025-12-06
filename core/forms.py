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




from django import forms
from django.forms import inlineformset_factory
from .models import WorkoutSession, WorkoutExercise, Exercise

class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['date', 'start_time', 'end_time', 'workout_type', 'notes', 'privacy']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'workout_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'How did it feel?'}),
            'privacy': forms.Select(attrs={'class': 'form-select'}),
        }

class WorkoutExerciseForm(forms.ModelForm):
    # This field accepts text. If it matches an existing exercise, it links it.
    # If not, the view/save method creates a new one.
    exercise_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'list': 'exercises-list', 
            'class': 'form-control exercise-search',
            'placeholder': 'Search or type new...',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = WorkoutExercise
        fields = ['exercise_name', 'sets', 'reps', 'reps_performed', 'weight_kg', 'order', 'notes']
        widgets = {
            'sets': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Sets'}),
            'reps': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Target (8-12)'}),
            'reps_performed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Done'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Kg'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes'}),
            'order': forms.HiddenInput(attrs={'class': 'exercise-order'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill the text input if editing
        if self.instance.pk and self.instance.exercise:
            self.fields['exercise_name'].initial = self.instance.exercise.name

    def save(self, commit=True):
        instance = super().save(commit=False)
        name = self.cleaned_data.get('exercise_name')
        if name:
            # Case-insensitive get-or-create
            exercise_obj, _ = Exercise.objects.get_or_create(
                name__iexact=name.strip(),
                defaults={'name': name.strip()}
            )
            instance.exercise = exercise_obj
        if commit:
            instance.save()
        return instance

WorkoutExerciseFormSet = inlineformset_factory(
    WorkoutSession, WorkoutExercise, form=WorkoutExerciseForm,
    extra=1, can_delete=True, can_order=False
)