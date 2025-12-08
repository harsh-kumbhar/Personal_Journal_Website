#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

python manage.py create_admin

echo "🌱 Seeding Database..."
python manage.py seed_home_data
python manage.py seed_workout_data
python manage.py link_workout_types  # Don't forget this one!
python manage.py seed_nutrition_data
python manage.py seed_academics_data
echo "✅ Seeding Complete."