from django.core.management.base import BaseCommand
from core.models import WorkoutType, Muscle

class Command(BaseCommand):
    help = "Links Workout Types to Muscles for smart filtering."

    def handle(self, *args, **options):
        # 1. Define the Mappings
        MAPPINGS = {
            "Push": ["Chest", "Shoulders", "Triceps"],
            "Pull": ["Back", "Biceps", "Forearms", "Traps", "Rear Delt"],
            "Legs": ["Quads", "Hamstrings", "Glutes", "Calves"],
            "Chest Day": ["Chest", "Triceps"],
            "Back Day": ["Back", "Biceps", "Traps"],
            "Leg Day": ["Quads", "Hamstrings", "Glutes", "Calves"],
            "Shoulder Day": ["Shoulders", "Traps"],
            "Arm Day": ["Biceps", "Triceps", "Forearms"],
            "Upper Body": ["Chest", "Back", "Shoulders", "Biceps", "Triceps"],
            "Lower Body": ["Quads", "Hamstrings", "Glutes", "Calves"],
            "Abs & Core": ["Abs", "Obliques", "Core"],
            "Cardio": ["Full Body", "Quads", "Calves"],
            "Full Body": ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"] # Logic handles partial matches
        }

        self.stdout.write("🔗 Linking Workout Types to Muscles...")

        for type_name, muscle_names in MAPPINGS.items():
            try:
                # Get the Workout Type
                w_type = WorkoutType.objects.get(name__icontains=type_name)
                
                # Find the Muscle objects
                muscles = Muscle.objects.filter(name__in=muscle_names)
                
                # Add them (M2M)
                w_type.targeted_muscles.add(*muscles)
                self.stdout.write(f"✅ Linked '{w_type.name}' to {muscles.count()} muscles.")
                
            except WorkoutType.DoesNotExist:
                # self.stdout.write(f"⚠️ Skipped '{type_name}' (Not found in DB)")
                pass
            except Exception as e:
                self.stdout.write(f"❌ Error with '{type_name}': {e}")

        self.stdout.write(self.style.SUCCESS("🎉 Linkage Complete! Dropdowns will now filter correctly."))