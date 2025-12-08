# core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum, F
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


# -------------------------
# Tag (generic small label)
# -------------------------
class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    color = models.CharField(max_length=7, blank=True, help_text="Optional hex color, e.g. #FF5733")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# Attachments (generic)
# -------------------------
class Attachment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    description = models.CharField(max_length=250, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.file.name} for {self.content_type}"


# -------------------------
# Workout / Exercise Models
# -------------------------
class Muscle(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name




class WorkoutType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    
    # --- NEW FIELD ---
    targeted_muscles = models.ManyToManyField('Muscle', blank=True, related_name='workout_types')
    
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Exercise(models.Model):
    name = models.CharField(max_length=200, unique=True)
    primary_muscle = models.ForeignKey(Muscle, null=True, blank=True, on_delete=models.SET_NULL, related_name='primary_exercises')
    secondary_muscles = models.ManyToManyField(Muscle, blank=True, related_name='secondary_exercises')
    default_sets = models.PositiveSmallIntegerField(null=True, blank=True)
    default_reps = models.CharField(max_length=50, blank=True, help_text="e.g. 8-12 or AMRAP")
    equipment = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class WorkoutSession(models.Model):
    """
    A single workout session entry (grouping of exercises performed on a date/time).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True,
                                                   help_text="Optional; auto-calculated if start and end provided.")
    location = models.CharField(max_length=200, blank=True)
    workout_type = models.ForeignKey(WorkoutType, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    privacy = models.CharField(max_length=20, choices=(('private','Private'),('public','Public')), default='private')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def save(self, *args, **kwargs):
        # Auto-calc duration if possible
        if self.start_time and self.end_time:
            # compute duration in minutes
            start_dt = timezone.datetime.combine(self.date, self.start_time)
            end_dt = timezone.datetime.combine(self.date, self.end_time)
            if end_dt < start_dt:
                # assume end is next day
                end_dt += timezone.timedelta(days=1)
            diff = end_dt - start_dt
            self.duration_minutes = int(diff.total_seconds() // 60)
        super().save(*args, **kwargs)

# In core/models.py inside WorkoutSession class:

    def total_volume(self):
        """
        Calculates Volume = Sets * Reps Performed * Weight (KG)
        Returns an integer (e.g. 5000) instead of float (5000.0)
        """
        q = self.exercises.aggregate(
            total=Sum(F('sets') * F('reps_performed') * F('weight_kg'), output_field=models.FloatField())
        )
        val = q.get('total') or 0.0
        return int(val)  # <--- Return simple integer here


class WorkoutExercise(models.Model):
    """
    One exercise performed within a WorkoutSession.
    'reps' is the plan (e.g., '8-12'), 'reps_performed' is the actual number for math.
    """
    workout = models.ForeignKey(WorkoutSession, related_name='exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=0, help_text='Order in workout')
    
    sets = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # The text field for the "Goal" or "Range" (e.g., "8-12", "AMRAP")
    reps = models.CharField(max_length=50, blank=True, help_text="Target reps (e.g. '8-12')")
    
    # The numeric field for actual volume calculation
    reps_performed = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Actual number of reps done (for volume calc)")
    
    weight_kg = models.FloatField(null=True, blank=True, help_text='Numeric weight in KG if applicable')
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    tempo = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['workout', 'order']),
        ]

    def __str__(self):
        return f"{self.exercise.name} ({self.workout.date})"
    
class PRRecord(models.Model):
    """
    Personal record per exercise (keeps track of best observed weight/reps).
    Optionally auto-updated by app logic when a bigger weight is logged.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    max_weight_kg = models.FloatField()
    reps_at_max = models.PositiveSmallIntegerField(null=True, blank=True)
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'exercise', 'date')
        indexes = [
            models.Index(fields=['user', 'exercise']),
        ]

    def __str__(self):
        return f"PR {self.exercise.name}: {self.max_weight_kg}kg on {self.date}"


# -------------------------
# Diet / Nutrition Models
# -------------------------
# core/models.py

# ... imports ...

class FoodItem(models.Model):
    # ... existing fields ...
    name = models.CharField(max_length=200)
    serving_size_desc = models.CharField(max_length=100, blank=True, help_text="e.g., '100g', '1 cup'")
    protein_per_100g = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    calories_per_100g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    carbs_per_100g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    fat_per_100g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    default_unit = models.CharField(max_length=50, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'serving_size_desc')
        ordering = ['name']

    # --- NEW PROPERTIES TO FIX FLOATING POINT ISSUE ---
    @property
    def protein_int(self):
        return int(self.protein_per_100g or 0)
    
    @property
    def calories_int(self):
        return int(self.calories_per_100g or 0)
        
    @property
    def carbs_int(self):
        return int(self.carbs_per_100g or 0)
    
    @property
    def fat_int(self):
        return int(self.fat_per_100g or 0)

    def __str__(self):
        return self.name


class DietEntry(models.Model):
    # ... existing fields ...
    MEAL_CHOICES = (
        ('breakfast','Breakfast'),
        ('lunch','Lunch'),
        ('dinner','Dinner'),
        ('snack','Snack'),
        ('other','Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_entries')
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES, default='other')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    # --- UPDATED METHODS TO RETURN INTEGERS DIRECTLY ---
    def total_protein(self):
        val = self.items.aggregate(total=Sum('protein_calculated'))['total'] or 0.0
        return int(val)

    def total_calories(self):
        val = self.items.aggregate(total=Sum('calories_calculated'))['total'] or 0.0
        return int(val)

    def __str__(self):
        return f"{self.date} {self.meal_type}"


class DietItem(models.Model):
    # ... existing fields ...
    diet_entry = models.ForeignKey(DietEntry, related_name='items', on_delete=models.CASCADE)
    food = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    amount = models.FloatField(validators=[MinValueValidator(0.0)], help_text="in grams (standardize in UI)")
    unit = models.CharField(max_length=40, blank=True, help_text="optional unit note")
    protein_calculated = models.FloatField(null=True, blank=True)
    calories_calculated = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['diet_entry', 'food']),
        ]

    def save(self, *args, **kwargs):
        # Compute macros based on per-100g values
        if self.food and self.amount is not None:
            self.protein_calculated = (self.food.protein_per_100g * self.amount) / 100.0
            if self.food.calories_per_100g is not None:
                self.calories_calculated = (self.food.calories_per_100g * self.amount) / 100.0
        super().save(*args, **kwargs)

    # --- NEW PROPERTIES FOR INTEGER DISPLAY ---
    @property
    def protein_int(self):
        return int(self.protein_calculated or 0)
    
    @property
    def calories_int(self):
        return int(self.calories_calculated or 0)

    def __str__(self):
        return f"{self.amount}g {self.food.name}"

class NutritionGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    daily_protein = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    daily_calories = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Goals for {self.user} (protein {self.daily_protein}g)"


class MealTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    items = models.ManyToManyField(FoodItem, through='MealTemplateItem')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MealTemplateItem(models.Model):
    template = models.ForeignKey(MealTemplate, on_delete=models.CASCADE)
    food = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.0)], help_text="in grams")
    order = models.PositiveSmallIntegerField(default=0)


# ... (Previous imports: User, models, timezone, etc.) ...

# -------------------------
# Academics / Internship Models
# -------------------------
class Topic(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    provider = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=True)
    certificate_url = models.URLField(blank=True)
    hours_estimated = models.FloatField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'title')
        ordering = ['-created_at']
    
    @property
    def hours_display(self):
        """Returns formatted string to avoid template filters"""
        val = self.hours_estimated or 0
        return f"{val:.1f}".rstrip('0').rstrip('.')

    def __str__(self):
        return self.title


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    tech_stack = models.CharField(max_length=300, blank=True, help_text="comma separated")
    repo_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=(('planning','Planning'),('active','Active'),('completed','Completed')), default='planning')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'title')

    def __str__(self):
        return self.title


class StudySession(models.Model):
    ACTIVITY_CHOICES = (
        ('dsa','DSA/Problem Solving'),
        ('reading','Reading'),
        ('project','Project Work'),
        ('internship','Internship'),
        ('course','Course Study'),
        ('other','Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_hours = models.FloatField(null=True, blank=True)
    activity_type = models.CharField(max_length=40, choices=ACTIVITY_CHOICES, default='other')
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL)
    topics = models.ManyToManyField(Topic, blank=True)
    pomodoro_sessions = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def save(self, *args, **kwargs):
        # compute duration if possible
        if self.start_time and self.end_time:
            start_dt = timezone.datetime.combine(self.date, self.start_time)
            end_dt = timezone.datetime.combine(self.date, self.end_time)
            if end_dt < start_dt:
                end_dt += timezone.timedelta(days=1)
            diff = end_dt - start_dt
            # Calculate hours
            self.duration_hours = round(diff.total_seconds() / 3600.0, 2)
        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        """Returns formatted string (e.g., '2.5') for templates"""
        val = self.duration_hours or 0.0
        # Format to 1 decimal place, remove trailing zero (2.0 -> 2, 2.5 -> 2.5)
        return f"{val:.2f}".rstrip('0').rstrip('.')

    def __str__(self):
        return f"{self.date} - {self.activity_type}"


class InternshipLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.FloatField(validators=[MinValueValidator(0.0)])
    task_title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL)
    deliverable_url = models.URLField(blank=True)
    billable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        
    @property
    def hours_display(self):
        """Returns formatted string to avoid template filters"""
        val = self.hours or 0
        return f"{val:.1f}".rstrip('0').rstrip('.')

    def __str__(self):
        return f"{self.date} - {self.task_title}"

# -------------------------
# General metrics & Habits
# -------------------------
class DailyMetrics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_metrics')
    date = models.DateField()
    water_ml = models.PositiveIntegerField(default=0, help_text="Total water consumed in ml")
    sleep_hours = models.FloatField(null=True, blank=True)
    screen_time_minutes = models.PositiveIntegerField(default=0)
    steps = models.PositiveIntegerField(null=True, blank=True)
    mood = models.CharField(max_length=50, blank=True)
    bad_habits = models.TextField(blank=True, help_text='Comma-separated or JSON for now')
    books_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user} - {self.date}"


class Habit(models.Model):
    FREQUENCY_CHOICES = (('daily','Daily'), ('weekly','Weekly'), ('monthly','Monthly'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=200)
    goal_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_done_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} on {self.date}"

# core/models.py
from django.contrib.contenttypes.models import ContentType
# ... existing imports ...

# Add these models near Habit / HabitLog definitions

class BadHabit(models.Model):
    """
    A bad habit definition the user tracks (e.g., 'Late-night snacking', 'Excess screen time').
    Created once and can be logged per day via BadHabitLog.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bad_habits')
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class BadHabitLog(models.Model):
    """
    A log entry that links a BadHabit to a specific date (one row per date/habit).
    """
    habit = models.ForeignKey(BadHabit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} on {self.date}"

class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    amount_ml = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.amount_ml}ml on {self.date}"


# -------------------------
# Journal / Quotes / Home
# -------------------------
class Quote(models.Model):
    text = models.TextField(unique=True)
    author = models.CharField(max_length=150, blank=True)
    source_url = models.URLField(blank=True)
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return (self.text[:80] + '...') if len(self.text) > 80 else self.text


class QuoteDisplayLog(models.Model):
    date = models.DateField(unique=True)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    shown_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote for {self.date}"


class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField()
    morning_note = models.TextField(blank=True)
    evening_note = models.TextField(blank=True)
    moment_of_day = models.TextField(blank=True)
    grateful_for = models.TextField(blank=True)
    regret = models.TextField(blank=True)
    highlights = models.TextField(blank=True)
    quote_added = models.ForeignKey(Quote, null=True, blank=True, on_delete=models.SET_NULL)
    mood = models.CharField(max_length=60, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date} Journal"


class QuickNote(models.Model):
    CATEGORY_CHOICES = (('idea','Idea'), ('todo','Todo'), ('memory','Memory'), ('other','Other'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quick_notes')
    content = models.TextField()
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.content[:60]}"


# -------------------------
# Reports, Exports & Backups
# -------------------------
class DailyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    json_snapshot = models.JSONField(blank=True, null=True)
    html_blob = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Report {self.user} - {self.date}"


class ExportJob(models.Model):
    TYPE_CHOICES = (('csv','CSV'), ('pdf','PDF'), ('json','JSON'))
    STATUS_CHOICES = (('pending','Pending'), ('running','Running'), ('done','Done'), ('failed','Failed'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Export {self.user} - {self.export_type} - {self.status}"


class BackupSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    note = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f"Backup {self.user} @ {self.created_at.strftime('%Y-%m-%d')}"


# -------------------------
# Cross-cutting / Settings / Notifications
# -------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=400)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')
    trigger_time = models.DateTimeField(null=True, blank=True)
    recurrence = models.JSONField(null=True, blank=True, help_text="Optional recurrence schema (daily/weekly)")
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    timezone = models.CharField(max_length=100, default='Asia/Kolkata')
    week_start = models.CharField(max_length=10, default='monday')
    protein_unit = models.CharField(max_length=10, default='g')
    weight_unit = models.CharField(max_length=10, default='kg')
    theme = models.CharField(max_length=20, default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user}"


# -------------------------
# Analytics / Aggregation Models (helpful later)
# -------------------------
class WeeklySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week_start_date = models.DateField()
    workout_count = models.PositiveIntegerField(default=0)
    study_hours = models.FloatField(default=0.0)
    protein_total = models.FloatField(default=0.0)
    avg_mood = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'week_start_date')


class ExerciseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    avg_weight = models.FloatField(null=True, blank=True)
    max_weight = models.FloatField(null=True, blank=True)
    volume = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'exercise']),
        ]

    def __str__(self):
        return f"Progress {self.exercise.name} ({self.period_start} - {self.period_end})"
