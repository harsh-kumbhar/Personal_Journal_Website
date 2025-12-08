# core/management/commands/seed_home_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core import models
from django.db import transaction

User = get_user_model()

# --- DATA LISTS ---

QUOTES = [
    # STOICISM & WISDOM
    {"text": "We suffer more often in imagination than in reality.", "author": "Seneca"},
    {"text": "It is not death that a man should fear, but he should fear never beginning to live.", "author": "Marcus Aurelius"},
    {"text": "Waste no more time arguing about what a good man should be. Be one.", "author": "Marcus Aurelius"},
    {"text": "He who has a why to live can bear almost any how.", "author": "Friedrich Nietzsche"},
    {"text": "No man is free who is not master of himself.", "author": "Epictetus"},
    {"text": "Man conquers the world by conquering himself.", "author": "Zeno of Citium"},
    {"text": "The best revenge is not to be like your enemy.", "author": "Marcus Aurelius"},
    {"text": "Dwell on the beauty of life. Watch the stars, and see yourself running with them.", "author": "Marcus Aurelius"},
    {"text": "It is not the man who has too little, but the man who craves more, that is poor.", "author": "Seneca"},
    {"text": "Luck is what happens when preparation meets opportunity.", "author": "Seneca"},

    # BODYBUILDING & DISCIPLINE
    {"text": "Everybody wants to be a bodybuilder, but nobody wants to lift no heavy-ass weights.", "author": "Ronnie Coleman"},
    {"text": "The worst thing I can be is the same as everybody else.", "author": "Arnold Schwarzenegger"},
    {"text": "The squat is the perfect analogy for life. It's about standing back up after something heavy takes you down.", "author": "Tom Platz"},
    {"text": "Light weight, baby!", "author": "Ronnie Coleman"},
    {"text": "The last three or four reps is what makes the muscle grow.", "author": "Arnold Schwarzenegger"},
    {"text": "Standard over feelings.", "author": "Chris Bumstead"},
    {"text": "It is the intensity of the effort that determines the result.", "author": "Mike Mentzer"},
    {"text": "Champions are built in the off-season.", "author": "Chris Bumstead"},
    {"text": "Whatever it takes.", "author": "Rich Piana"},
    {"text": "I don't eat for taste, I eat for function.", "author": "Jay Cutler"},
    {"text": "Ain't nothing to it but to do it.", "author": "Ronnie Coleman"},
    {"text": "You have to be willing to fail to succeed.", "author": "Tom Platz"},
    {"text": "Vision creates faith and faith creates willpower.", "author": "Arnold Schwarzenegger"},
    
    # PRODUCTIVITY & ACTION
    {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
    {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    {"text": "Act as if what you do makes a difference. It does.", "author": "William James"},
    {"text": "Do not wait to strike till the iron is hot; but make it hot by striking.", "author": "William Butler Yeats"},
    {"text": "Great acts are made up of small deeds.", "author": "Lao Tzu"},
    {"text": "The journey of a thousand miles begins with one step.", "author": "Lao Tzu"},
    {"text": "The best way to predict the future is to create it.", "author": "Peter Drucker"},
    {"text": "You miss 100% of the shots you don't take.", "author": "Wayne Gretzky"},
    {"text": "Everything you’ve ever wanted is on the other side of fear.", "author": "George Addair"},
    {"text": "Don’t let yesterday take up too much of today.", "author": "Will Rogers"},
    {"text": "Discipline is the bridge between goals and accomplishment.", "author": "Jim Rohn"},
    {"text": "Motivation is what gets you started. Habit is what keeps you going.", "author": "Jim Ryun"},
    {"text": "Don't wish it were easier. Wish you were better.", "author": "Jim Rohn"},
    {"text": "Your time is limited, so don't waste it living someone else's life.", "author": "Steve Jobs"},
    {"text": "Simplicity is the ultimate sophistication.", "author": "Leonardo da Vinci"},
    {"text": "Focus on the process, not the outcome.", "author": "Unknown"},
    {"text": "Consistent action creates consistent results.", "author": "Unknown"},
    {"text": "Be so good they can't ignore you.", "author": "Steve Martin"},
    {"text": "Amateurs sit and wait for inspiration, the rest of us just get up and go to work.", "author": "Stephen King"},
    {"text": "Action is the foundational key to all success.", "author": "Pablo Picasso"},
    {"text": "Doubt kills more dreams than failure ever will.", "author": "Suzy Kassem"},
    {"text": "Stay hungry. Stay foolish.", "author": "Steve Jobs"},
    {"text": "If you're going through hell, keep going.", "author": "Winston Churchill"},
    {"text": "Make each day your masterpiece.", "author": "John Wooden"},
    {"text": "Dream big and dare to fail.", "author": "Norman Vaughan"},
]

# Habits to track (Structure only, no logs)
DEFAULT_HABITS = [
    {"name": "Read 10 Pages", "frequency": "daily"},
    {"name": "Meditate 10 Mins", "frequency": "daily"},
    {"name": "Drink 3L Water", "frequency": "daily"},
    {"name": "Weekly Review", "frequency": "weekly"},
    {"name": "No Sugar", "frequency": "daily"},
]

DEFAULT_BAD_HABITS = [
    {"name": "Doomscrolling"},
    {"name": "Late Night Snacking"},
    {"name": "Procrastination"},
]

SAMPLE_NOTES = [
    {"content": "Idea for a new project: AI-based recipe generator.", "category": "idea"},
    {"content": "Buy groceries: Milk, Eggs, Spinach, Chicken.", "category": "todo"},
    {"content": "Remember to call Mom this weekend.", "category": "memory"},
]

class Command(BaseCommand):
    help = "Seed initial data for Home/Journal (Quotes, Habits Config, Notes, Settings)."

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding Home Data (Structure Only)...")

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("❌ No users found! Please run 'python manage.py createsuperuser' first."))
            return

        self.stdout.write(f"👤 Using User: {user.username}")

        with transaction.atomic():
            # 1. QUOTES
            count = 0
            for q in QUOTES:
                obj, created = models.Quote.objects.get_or_create(
                    text=q['text'], 
                    defaults={
                        'author': q.get('author', ''),
                        'approved': True,
                        'added_by': user
                    }
                )
                if created:
                    count += 1
            self.stdout.write(f"✅ Created {count} Quotes.")

            # 2. HABIT DEFINITIONS (Empty streaks, ready for you to track)
            for h in DEFAULT_HABITS:
                models.Habit.objects.get_or_create(
                    user=user, 
                    name=h['name'], 
                    defaults={
                        'goal_frequency': h['frequency'],
                        'current_streak': 0,
                        'best_streak': 0
                    }
                )
            self.stdout.write(f"✅ Created {len(DEFAULT_HABITS)} Default Habits.")

            # 3. BAD HABIT DEFINITIONS
            for bh in DEFAULT_BAD_HABITS:
                models.BadHabit.objects.get_or_create(
                    user=user, 
                    name=bh['name'],
                    defaults={'active': True}
                )
            self.stdout.write(f"✅ Created {len(DEFAULT_BAD_HABITS)} Bad Habits.")

            # 4. SAMPLE NOTES
            for note in SAMPLE_NOTES:
                models.QuickNote.objects.get_or_create(
                    user=user,
                    content=note['content'],
                    defaults={'category': note['category']}
                )
            self.stdout.write(f"✅ Created Sample Notes.")

            # 5. USER SETTINGS (Ensure defaults exist)
            settings, created = models.UserSettings.objects.get_or_create(
                user=user,
                defaults={
                    'theme': 'dark',
                    'weight_unit': 'kg',
                    'protein_unit': 'g'
                }
            )
            if created:
                self.stdout.write(f"✅ Initialized User Settings.")

            # 6. WELCOME NOTIFICATION
            models.Notification.objects.create(
                user=user,
                message="Welcome to your new Journal! Start by logging your first workout.",
                sent=False,
                trigger_time=timezone.now()
            )
            self.stdout.write(f"✅ Sent Welcome Notification.")

        self.stdout.write(self.style.SUCCESS("🎉 Home Page Seeding Complete! (No fake daily logs added)"))