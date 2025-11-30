# core/management/commands/seed_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core import models
from django.db import transaction

User = get_user_model()

WORKOUT_TYPES = [
    "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Full Body", "Cardio", "Mobility", "HIIT", "Warmup", "Cooldown"
]

MUSCLES = [
    "Pectoralis Major", "Latissimus Dorsi", "Quadriceps", "Hamstrings", "Deltoids", "Biceps", "Triceps", "Glutes", "Core"
]

EXERCISES = [
    {"name":"Bench Press","primary":"Pectoralis Major"},
    {"name":"Barbell Row","primary":"Latissimus Dorsi"},
    {"name":"Squat","primary":"Quadriceps"},
    {"name":"Deadlift","primary":"Hamstrings"},
    {"name":"Overhead Press","primary":"Deltoids"},
    {"name":"Pull Up","primary":"Latissimus Dorsi"},
    {"name":"Push Up","primary":"Pectoralis Major"},
    {"name":"Dumbbell Curl","primary":"Biceps"},
    {"name":"Tricep Dip","primary":"Triceps"},
    {"name":"Plank","primary":"Core"},
]

FOODS = [
    {"name":"Chicken Breast","protein":31.0,"calories":165,"serving":"100g"},
    {"name":"Egg (whole)","protein":13.0,"calories":155,"serving":"100g"},
    {"name":"Rice (cooked)","protein":2.7,"calories":130,"serving":"100g"},
    {"name":"Brown Bread","protein":8.0,"calories":265,"serving":"100g"},
    {"name":"Greek Yogurt","protein":10.0,"calories":59,"serving":"100g"},
    {"name":"Whey Protein (powder)","protein":80.0,"calories":400,"serving":"100g"},
    {"name":"Almonds","protein":21.0,"calories":579,"serving":"100g"},
]

QUOTES = [
    {"text":"Small daily improvements are the key to staggering long-term results.","author":"Unknown"},
    {"text":"Discipline is choosing between what you want now and what you want most.","author":"Abraham Lincoln (attributed)"},
    {"text":"You don't have to be great to start, but you have to start to be great.","author":"Zig Ziglar"},
]

TAGS = ["strength","hypertrophy","endurance","mobility","cardio","home","gym"]

class Command(BaseCommand):
    help = "Seed initial lookup data (workout types, muscles, exercises, foods, quotes, tags)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding initial data...")

        with transaction.atomic():
            # Workout types
            for name in WORKOUT_TYPES:
                obj, created = models.WorkoutType.objects.get_or_create(name=name)
                if created:
                    self.stdout.write(f"Created WorkoutType: {name}")

            # Muscles
            muscle_map = {}
            for m in MUSCLES:
                obj, created = models.Muscle.objects.get_or_create(name=m)
                muscle_map[m] = obj
                if created:
                    self.stdout.write(f"Created Muscle: {m}")

            # Exercises
            for ex in EXERCISES:
                prim = muscle_map.get(ex['primary'])
                obj, created = models.Exercise.objects.get_or_create(name=ex['name'], defaults={
                    'primary_muscle': prim
                })
                if created:
                    self.stdout.write(f"Created Exercise: {ex['name']}")

            # Foods
            for f in FOODS:
                obj, created = models.FoodItem.objects.get_or_create(
                    name=f['name'],
                    serving_size_desc=f['serving'],
                    defaults={
                        'protein_per_100g': f['protein'],
                        'calories_per_100g': f['calories']
                    }
                )
                if created:
                    self.stdout.write(f"Created FoodItem: {f['name']}")

            # Quotes
            for q in QUOTES:
                obj, created = models.Quote.objects.get_or_create(text=q['text'], defaults={'author': q.get('author','')})
                if created:
                    self.stdout.write(f"Created Quote: {q['text'][:50]}")

            # Tags
            for t in TAGS:
                obj, created = models.Tag.objects.get_or_create(name=t)
                if created:
                    self.stdout.write(f"Created Tag: {t}")

        self.stdout.write(self.style.SUCCESS("Seeding done."))
