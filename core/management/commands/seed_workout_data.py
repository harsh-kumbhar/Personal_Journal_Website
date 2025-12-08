# core/management/commands/seed_workout_data.py
from django.core.management.base import BaseCommand
from core import models
from django.db import transaction

# --- 1. WORKOUT TYPES (Comprehensive) ---
WORKOUT_TYPES = [
    # The Classics
    "Chest Day", "Back Day", "Leg Day", "Arm Day", "Shoulder Day",
    # The Splits
    "Push", "Pull", "Legs (Split)", "Upper Body", "Lower Body",
    # Styles & Goals
    "Full Body", "Cardio", "HIIT", "CrossFit", "Powerlifting", 
    "Calisthenics", "Mobility / Stretching", "Recovery", "Abs & Core"
]

# --- 2. BASIC MUSCLE NAMES (Everyday Terms) ---
MUSCLES = [
    "Chest", 
    "Back", 
    "Shoulders", 
    "Biceps", 
    "Triceps", 
    "Forearms",
    "Traps", 
    "Quads", 
    "Hamstrings", 
    "Glutes", 
    "Calves", 
    "Abs", 
    "Lower Back",
    "Full Body", # For cardio/compound movements
    "Neck"
]

# --- 3. MASSIVE EXERCISE LIBRARY ---
EXERCISES = [
    # --- CHEST ---
    {"name": "Bench Press (Barbell)", "primary": "Chest"},
    {"name": "Bench Press (Dumbbell)", "primary": "Chest"},
    {"name": "Incline Bench Press (Barbell)", "primary": "Chest"},
    {"name": "Incline Bench Press (Dumbbell)", "primary": "Chest"},
    {"name": "Decline Bench Press", "primary": "Chest"},
    {"name": "Chest Fly (Dumbbell)", "primary": "Chest"},
    {"name": "Chest Fly (Cable)", "primary": "Chest"},
    {"name": "Pec Deck Machine", "primary": "Chest"},
    {"name": "Push Ups", "primary": "Chest"},
    {"name": "Weighted Push Ups", "primary": "Chest"},
    {"name": "Dips (Chest Focus)", "primary": "Chest"},
    {"name": "Landmine Press", "primary": "Chest"},
    {"name": "Pullover (Dumbbell)", "primary": "Chest"},
    {"name": "Smith Machine Bench Press", "primary": "Chest"},

    # --- BACK ---
    {"name": "Pull Up", "primary": "Back"},
    {"name": "Chin Up", "primary": "Back"},
    {"name": "Lat Pulldown (Wide Grip)", "primary": "Back"},
    {"name": "Lat Pulldown (Close Grip)", "primary": "Back"},
    {"name": "Barbell Row", "primary": "Back"},
    {"name": "Dumbbell Row (Single Arm)", "primary": "Back"},
    {"name": "Seated Cable Row", "primary": "Back"},
    {"name": "T-Bar Row", "primary": "Back"},
    {"name": "Chest Supported Row", "primary": "Back"},
    {"name": "Face Pull", "primary": "Back"},
    {"name": "Straight Arm Pulldown", "primary": "Back"},
    {"name": "Deadlift (Conventional)", "primary": "Lower Back"},
    {"name": "Deadlift (Sumo)", "primary": "Lower Back"},
    {"name": "Back Extension (Hyperextension)", "primary": "Lower Back"},
    {"name": "Rack Pull", "primary": "Back"},

    # --- SHOULDERS ---
    {"name": "Overhead Press (Barbell)", "primary": "Shoulders"},
    {"name": "Seated Dumbbell Press", "primary": "Shoulders"},
    {"name": "Arnold Press", "primary": "Shoulders"},
    {"name": "Lateral Raise (Dumbbell)", "primary": "Shoulders"},
    {"name": "Lateral Raise (Cable)", "primary": "Shoulders"},
    {"name": "Front Raise", "primary": "Shoulders"},
    {"name": "Rear Delt Fly (Dumbbell)", "primary": "Shoulders"},
    {"name": "Rear Delt Fly (Machine)", "primary": "Shoulders"},
    {"name": "Upright Row", "primary": "Shoulders"},
    {"name": "Egyptian Lateral Raise", "primary": "Shoulders"},
    {"name": "Shrugs (Barbell)", "primary": "Traps"},
    {"name": "Shrugs (Dumbbell)", "primary": "Traps"},

    # --- BICEPS ---
    {"name": "Barbell Curl", "primary": "Biceps"},
    {"name": "Dumbbell Curl", "primary": "Biceps"},
    {"name": "Hammer Curl", "primary": "Biceps"},
    {"name": "Preacher Curl", "primary": "Biceps"},
    {"name": "Concentration Curl", "primary": "Biceps"},
    {"name": "Incline Dumbbell Curl", "primary": "Biceps"},
    {"name": "Cable Curl", "primary": "Biceps"},
    {"name": "Spider Curl", "primary": "Biceps"},
    {"name": "EZ Bar Curl", "primary": "Biceps"},
    {"name": "Chin Ups (Weighted)", "primary": "Biceps"},

    # --- TRICEPS ---
    {"name": "Tricep Pushdown (Rope)", "primary": "Triceps"},
    {"name": "Tricep Pushdown (Bar)", "primary": "Triceps"},
    {"name": "Skullcrushers", "primary": "Triceps"},
    {"name": "Overhead Extension (Dumbbell)", "primary": "Triceps"},
    {"name": "Overhead Extension (Cable)", "primary": "Triceps"},
    {"name": "Close Grip Bench Press", "primary": "Triceps"},
    {"name": "Dips (Tricep Focus)", "primary": "Triceps"},
    {"name": "Tricep Kickback", "primary": "Triceps"},
    {"name": "Diamond Push Up", "primary": "Triceps"},

    # --- LEGS (QUADS) ---
    {"name": "Squat (Barbell Back)", "primary": "Quads"},
    {"name": "Squat (Front)", "primary": "Quads"},
    {"name": "Leg Press", "primary": "Quads"},
    {"name": "Goblet Squat", "primary": "Quads"},
    {"name": "Bulgarian Split Squat", "primary": "Quads"},
    {"name": "Lunges (Walking)", "primary": "Quads"},
    {"name": "Lunges (Reverse)", "primary": "Quads"},
    {"name": "Leg Extension", "primary": "Quads"},
    {"name": "Hack Squat", "primary": "Quads"},
    {"name": "Step Ups", "primary": "Quads"},

    # --- LEGS (HAMSTRINGS & GLUTES) ---
    {"name": "Romanian Deadlift (RDL)", "primary": "Hamstrings"},
    {"name": "Leg Curl (Seated)", "primary": "Hamstrings"},
    {"name": "Leg Curl (Lying)", "primary": "Hamstrings"},
    {"name": "Hip Thrust (Barbell)", "primary": "Glutes"},
    {"name": "Glute Bridge", "primary": "Glutes"},
    {"name": "Cable Pull Through", "primary": "Glutes"},
    {"name": "Good Morning", "primary": "Hamstrings"},
    {"name": "Kettlebell Swing", "primary": "Hamstrings"},

    # --- CALVES ---
    {"name": "Standing Calf Raise", "primary": "Calves"},
    {"name": "Seated Calf Raise", "primary": "Calves"},
    {"name": "Donkey Calf Raise", "primary": "Calves"},
    {"name": "Leg Press Calf Raise", "primary": "Calves"},

    # --- ABS / CORE ---
    {"name": "Plank", "primary": "Abs"},
    {"name": "Crunches", "primary": "Abs"},
    {"name": "Hanging Leg Raise", "primary": "Abs"},
    {"name": "Cable Crunch", "primary": "Abs"},
    {"name": "Russian Twist", "primary": "Abs"},
    {"name": "Ab Wheel Rollout", "primary": "Abs"},
    {"name": "Bicycle Crunches", "primary": "Abs"},
    {"name": "Dragon Flag", "primary": "Abs"},
    {"name": "Woodchoppers", "primary": "Abs"},

    # --- FOREARMS ---
    {"name": "Wrist Curls", "primary": "Forearms"},
    {"name": "Reverse Curls", "primary": "Forearms"},
    {"name": "Farmers Walk", "primary": "Forearms"},
    {"name": "Dead Hang", "primary": "Forearms"},

    # --- CARDIO / FULL BODY ---
    {"name": "Running (Treadmill)", "primary": "Full Body"},
    {"name": "Cycling", "primary": "Quads"},
    {"name": "Rowing Machine", "primary": "Full Body"},
    {"name": "Jump Rope", "primary": "Calves"},
    {"name": "Stairmaster", "primary": "Glutes"},
    {"name": "Burpees", "primary": "Full Body"},
    {"name": "Battle Ropes", "primary": "Shoulders"},
]

class Command(BaseCommand):
    help = "Seed comprehensive workout data with everyday gym terms."

    def handle(self, *args, **options):
        self.stdout.write("🏋️  Seeding Massive Workout Library...")

        with transaction.atomic():
            # 1. Workout Types
            count_types = 0
            for name in WORKOUT_TYPES:
                obj, created = models.WorkoutType.objects.get_or_create(name=name)
                if created:
                    count_types += 1
            self.stdout.write(f"✅ Created {count_types} Workout Types.")

            # 2. Muscles
            muscle_map = {}
            count_muscles = 0
            for m in MUSCLES:
                obj, created = models.Muscle.objects.get_or_create(name=m)
                muscle_map[m] = obj
                if created:
                    count_muscles += 1
            self.stdout.write(f"✅ Created {count_muscles} Muscles.")

            # 3. Exercises
            count_exercises = 0
            for ex in EXERCISES:
                target_muscle_name = ex['primary']
                primary_muscle_obj = muscle_map.get(target_muscle_name)

                # Safety check
                if not primary_muscle_obj:
                    self.stdout.write(self.style.WARNING(f"⚠️  Muscle '{target_muscle_name}' not found for exercise '{ex['name']}'. Skipping."))
                    continue

                obj, created = models.Exercise.objects.get_or_create(
                    name=ex['name'], 
                    defaults={
                        'primary_muscle': primary_muscle_obj,
                    }
                )
                if created:
                    count_exercises += 1
            
            self.stdout.write(f"✅ Created {count_exercises} Exercises.")

        self.stdout.write(self.style.SUCCESS("🎉 Workout Database Seeding Complete!"))