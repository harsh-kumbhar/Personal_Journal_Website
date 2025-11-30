# core/forms.py
from django import forms
from .models import JournalEntry, QuickNote, Quote

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'moment_of_day', 'grateful_for', 'regret', 'highlights', 'quote_added', 'mood']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
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
            'content': forms.Textarea(attrs={'rows':2, 'placeholder':'Quick idea / todo...'}),
        }

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['text', 'author']
        widgets = {
            'text': forms.Textarea(attrs={'rows':2, 'placeholder':'Write a quote...'}),
            'author': forms.TextInput(attrs={'placeholder':'Author (optional)'}),
        }
