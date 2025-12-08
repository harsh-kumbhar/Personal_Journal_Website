# core/management/commands/seed_nutrition_data.py
from django.core.management.base import BaseCommand
from core import models
from django.db import transaction

# --- THE MASSIVE FOOD DATABASE (Per 100g) ---
# Format: Name, Serving Desc, Protein, Cals, Carbs, Fat

FOOD_DATABASE = [
    # --- PROTEIN SOURCES (MEAT/POULTRY) ---
    {"name": "Chicken Breast (Cooked)", "serving": "100g", "p": 31.0, "cals": 165, "c": 0.0, "f": 3.6},
    {"name": "Chicken Breast (Raw)", "serving": "100g", "p": 23.0, "cals": 110, "c": 0.0, "f": 1.2},
    {"name": "Chicken Thigh (Cooked)", "serving": "100g", "p": 24.0, "cals": 209, "c": 0.0, "f": 10.9},
    {"name": "Ground Beef (90% Lean)", "serving": "100g", "p": 26.0, "cals": 217, "c": 0.0, "f": 11.0},
    {"name": "Ground Beef (80% Lean)", "serving": "100g", "p": 25.0, "cals": 254, "c": 0.0, "f": 20.0},
    {"name": "Steak (Sirloin, Trimmed)", "serving": "100g", "p": 29.0, "cals": 200, "c": 0.0, "f": 10.0},
    {"name": "Turkey Breast (Cooked)", "serving": "100g", "p": 29.0, "cals": 135, "c": 0.0, "f": 1.0},
    {"name": "Bacon (Pan-fried)", "serving": "100g", "p": 37.0, "cals": 541, "c": 1.4, "f": 42.0},
    
    # --- SEAFOOD ---
    {"name": "Salmon (Atlantic, Raw)", "serving": "100g", "p": 20.0, "cals": 208, "c": 0.0, "f": 13.0},
    {"name": "Tuna (Canned in Water)", "serving": "100g", "p": 24.0, "cals": 116, "c": 0.0, "f": 1.0},
    {"name": "Tilapia (Cooked)", "serving": "100g", "p": 26.0, "cals": 129, "c": 0.0, "f": 2.7},
    {"name": "Shrimp (Cooked)", "serving": "100g", "p": 24.0, "cals": 99, "c": 0.2, "f": 0.3},
    {"name": "Cod (Atlantic, Cooked)", "serving": "100g", "p": 23.0, "cals": 105, "c": 0.0, "f": 0.9},

    # --- EGGS & DAIRY ---
    {"name": "Egg (Whole, Large)", "serving": "1 large (50g)", "p": 13.0, "cals": 155, "c": 1.1, "f": 11.0},
    {"name": "Egg Whites (Liquid)", "serving": "100g", "p": 11.0, "cals": 52, "c": 0.7, "f": 0.2},
    {"name": "Greek Yogurt (Non-Fat)", "serving": "100g", "p": 10.0, "cals": 59, "c": 3.6, "f": 0.4},
    {"name": "Cottage Cheese (Low Fat)", "serving": "100g", "p": 11.0, "cals": 81, "c": 4.0, "f": 2.3},
    {"name": "Whole Milk", "serving": "100ml", "p": 3.2, "cals": 61, "c": 4.8, "f": 3.3},
    {"name": "Skim Milk", "serving": "100ml", "p": 3.4, "cals": 35, "c": 5.0, "f": 0.1},
    {"name": "Cheddar Cheese", "serving": "100g", "p": 25.0, "cals": 402, "c": 1.3, "f": 33.0},
    {"name": "Mozzarella Cheese", "serving": "100g", "p": 22.0, "cals": 280, "c": 2.2, "f": 17.0},
    {"name": "Paneer (Raw)", "serving": "100g", "p": 18.0, "cals": 265, "c": 1.2, "f": 20.0},

    # --- VEGAN / VEGETARIAN PROTEIN ---
    {"name": "Tofu (Firm)", "serving": "100g", "p": 17.0, "cals": 144, "c": 3.0, "f": 8.7},
    {"name": "Lentils (Cooked)", "serving": "100g", "p": 9.0, "cals": 116, "c": 20.0, "f": 0.4},
    {"name": "Chickpeas (Cooked)", "serving": "100g", "p": 8.9, "cals": 164, "c": 27.0, "f": 2.6},
    {"name": "Black Beans (Cooked)", "serving": "100g", "p": 8.9, "cals": 132, "c": 23.7, "f": 0.5},
    {"name": "Edamame (Shelled)", "serving": "100g", "p": 11.0, "cals": 121, "c": 10.0, "f": 5.0},
    {"name": "Soya Chunks (Raw)", "serving": "100g", "p": 52.0, "cals": 345, "c": 33.0, "f": 0.5},

    # --- SUPPLEMENTS ---
    {"name": "Whey Protein Isolate", "serving": "1 scoop (30g)", "p": 88.0, "cals": 370, "c": 1.0, "f": 1.0},
    {"name": "Whey Protein Concentrate", "serving": "1 scoop (30g)", "p": 75.0, "cals": 400, "c": 6.0, "f": 6.0},
    {"name": "Casein Protein", "serving": "1 scoop (30g)", "p": 73.0, "cals": 360, "c": 4.0, "f": 2.0},
    {"name": "Creatine Monohydrate", "serving": "5g", "p": 0.0, "cals": 0, "c": 0.0, "f": 0.0},

    # --- CARB SOURCES (GRAINS/STARCH) ---
    {"name": "White Rice (Cooked)", "serving": "100g", "p": 2.7, "cals": 130, "c": 28.0, "f": 0.3},
    {"name": "Brown Rice (Cooked)", "serving": "100g", "p": 2.6, "cals": 111, "c": 23.0, "f": 0.9},
    {"name": "Basmati Rice (Cooked)", "serving": "100g", "p": 3.5, "cals": 121, "c": 25.0, "f": 0.4},
    {"name": "Oats (Rolled, Raw)", "serving": "100g", "p": 16.9, "cals": 389, "c": 66.0, "f": 6.9},
    {"name": "Sweet Potato (Baked)", "serving": "100g", "p": 1.6, "cals": 90, "c": 20.7, "f": 0.1},
    {"name": "Potato (White, Baked)", "serving": "100g", "p": 2.0, "cals": 93, "c": 21.0, "f": 0.1},
    {"name": "Quinoa (Cooked)", "serving": "100g", "p": 4.4, "cals": 120, "c": 21.3, "f": 1.9},
    {"name": "Whole Wheat Bread", "serving": "1 slice", "p": 13.0, "cals": 247, "c": 41.0, "f": 3.4},
    {"name": "White Bread", "serving": "1 slice", "p": 9.0, "cals": 265, "c": 49.0, "f": 3.2},
    {"name": "Pasta (White, Cooked)", "serving": "100g", "p": 5.8, "cals": 131, "c": 25.0, "f": 1.1},
    
    # --- FRUITS ---
    {"name": "Banana", "serving": "1 medium", "p": 1.1, "cals": 89, "c": 22.8, "f": 0.3},
    {"name": "Apple (Red)", "serving": "1 medium", "p": 0.3, "cals": 52, "c": 14.0, "f": 0.2},
    {"name": "Blueberries", "serving": "100g", "p": 0.7, "cals": 57, "c": 14.0, "f": 0.3},
    {"name": "Strawberries", "serving": "100g", "p": 0.7, "cals": 32, "c": 7.7, "f": 0.3},
    {"name": "Watermelon", "serving": "100g", "p": 0.6, "cals": 30, "c": 7.6, "f": 0.2},
    {"name": "Orange", "serving": "1 medium", "p": 0.9, "cals": 47, "c": 11.8, "f": 0.1},
    {"name": "Avocado", "serving": "100g", "p": 2.0, "cals": 160, "c": 8.5, "f": 14.7},

    # --- VEGETABLES ---
    {"name": "Broccoli (Steamed)", "serving": "100g", "p": 2.8, "cals": 35, "c": 7.2, "f": 0.4},
    {"name": "Spinach (Raw)", "serving": "100g", "p": 2.9, "cals": 23, "c": 3.6, "f": 0.4},
    {"name": "Asparagus (Cooked)", "serving": "100g", "p": 2.4, "cals": 22, "c": 4.1, "f": 0.2},
    {"name": "Carrots (Raw)", "serving": "100g", "p": 0.9, "cals": 41, "c": 9.6, "f": 0.2},
    {"name": "Cucumber", "serving": "100g", "p": 0.7, "cals": 15, "c": 3.6, "f": 0.1},
    {"name": "Bell Pepper (Red)", "serving": "100g", "p": 1.0, "cals": 31, "c": 6.0, "f": 0.3},

    # --- NUTS & FATS ---
    {"name": "Almonds", "serving": "100g", "p": 21.0, "cals": 579, "c": 21.6, "f": 49.9},
    {"name": "Walnuts", "serving": "100g", "p": 15.0, "cals": 654, "c": 13.7, "f": 65.2},
    {"name": "Peanut Butter", "serving": "100g", "p": 25.0, "cals": 588, "c": 20.0, "f": 50.0},
    {"name": "Olive Oil", "serving": "1 tbsp (14g)", "p": 0.0, "cals": 884, "c": 0.0, "f": 100.0},
    {"name": "Butter", "serving": "1 tbsp (14g)", "p": 0.9, "cals": 717, "c": 0.1, "f": 81.1},
    {"name": "Coconut Oil", "serving": "1 tbsp", "p": 0.0, "cals": 892, "c": 0.0, "f": 99.0},

    # --- SNACKS / TREATS ---
    {"name": "Dark Chocolate (70%)", "serving": "100g", "p": 7.8, "cals": 598, "c": 46.0, "f": 43.0},
    {"name": "Milk Chocolate", "serving": "100g", "p": 7.7, "cals": 535, "c": 59.0, "f": 30.0},
    {"name": "Pizza (Cheese)", "serving": "1 slice", "p": 11.0, "cals": 266, "c": 33.0, "f": 10.0},
    {"name": "Burger (Fast Food)", "serving": "1 item", "p": 13.0, "cals": 254, "c": 30.0, "f": 9.0},
    {"name": "Popcorn (Air Popped)", "serving": "100g", "p": 12.0, "cals": 387, "c": 77.0, "f": 4.5},
]

class Command(BaseCommand):
    help = "Seed massive nutrition database (100+ items)."

    def handle(self, *args, **options):
        self.stdout.write("🥗 Seeding Food Library...")

        with transaction.atomic():
            count = 0
            for food in FOOD_DATABASE:
                obj, created = models.FoodItem.objects.get_or_create(
                    name=food['name'],
                    defaults={
                        'serving_size_desc': food['serving'],
                        'protein_per_100g': food['p'],
                        'calories_per_100g': food['cals'],
                        'carbs_per_100g': food['c'],
                        'fat_per_100g': food['f']
                    }
                )
                if created:
                    count += 1
            
            self.stdout.write(f"✅ Successfully added {count} new food items to the library.")
            self.stdout.write(f"📊 Total items in database: {models.FoodItem.objects.count()}")

        self.stdout.write(self.style.SUCCESS("🎉 Nutrition Data Seeding Complete!"))