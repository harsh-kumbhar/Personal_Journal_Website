# core/management/commands/seed_academics_data.py
from django.core.management.base import BaseCommand
from core import models
from django.db import transaction

# --- TOPIC LIBRARY (For Study Sessions) ---
# Organized by category for code readability, but they all go into the 'Topic' model.
TOPICS = [
    # Programming Languages
    "Python", "JavaScript", "Java", "C++", "C", "Go", "Rust", "TypeScript", 
    "Swift", "Kotlin", "PHP", "Ruby", "SQL", "HTML/CSS", "Bash/Shell",

    # Web Development (Frontend/Backend)
    "Django", "Flask", "FastAPI", "React", "Next.js", "Vue.js", "Angular", 
    "Node.js", "Express", "Spring Boot", "ASP.NET", "Tailwind CSS", "Bootstrap",
    "GraphQL", "WebSockets", "Microservices", "API Design",

    # Computer Science Fundamentals
    "Data Structures", "Algorithms", "System Design", "Operating Systems", 
    "Computer Networks", "Database Management", "Distributed Systems", 
    "Compiler Design", "Computer Architecture", "Discrete Math", 
    "Object-Oriented Programming (OOP)", "Design Patterns",

    # Data Science & AI
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP", 
    "Computer Vision", "Pandas", "NumPy", "PyTorch", "TensorFlow", 
    "Data Visualization", "Statistics", "Big Data",

    # DevOps & Tools
    "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", 
    "CI/CD", "Linux", "Nginx", "Redis", "Kafka", "Elasticsearch", "Terraform",

    # Cybersecurity
    "Network Security", "Cryptography", "Ethical Hacking", "OWASP", 
    "Penetration Testing", "Security Operations",

    # Mobile & Game Dev
    "Android Development", "iOS Development", "Flutter", "React Native", 
    "Unity", "Unreal Engine", "Game Design",

    # Soft Skills & Career
    "Interview Prep", "Resume Building", "System Design Interview", 
    "Technical Writing", "Public Speaking", "Project Management (Agile/Scrum)"
]

# --- ACADEMIC TAGS (For Courses/Projects) ---
ACADEMIC_TAGS = [
    # Course Formats
    "Online Course", "University", "Bootcamp", "Tutorial", "Documentation", "Book",
    
    # Status/Type
    "Certification", "Degree", "Self-Taught", "Workshop", "Seminar",
    
    # Assessment
    "Exam Prep", "Assignment", "Capstone", "Research", "Thesis"
]

class Command(BaseCommand):
    help = "Seed initial Topics and Tags for Academics (No user logs)."

    def handle(self, *args, **options):
        self.stdout.write("🎓 Seeding Academics Library...")

        with transaction.atomic():
            # 1. SEED TOPICS
            count_topics = 0
            for name in TOPICS:
                obj, created = models.Topic.objects.get_or_create(name=name)
                if created:
                    count_topics += 1
            self.stdout.write(f"✅ Created {count_topics} new Topics.")

            # 2. SEED ACADEMIC TAGS
            count_tags = 0
            for name in ACADEMIC_TAGS:
                # We use the generic Tag model, maybe with a specific color if desired, 
                # but for now just name is enough.
                obj, created = models.Tag.objects.get_or_create(
                    name=name,
                    defaults={'color': '#333333'} # Default dark grey for academics
                )
                if created:
                    count_tags += 1
            self.stdout.write(f"✅ Created {count_tags} new Academic Tags.")
            
            # 3. STATS
            total_topics = models.Topic.objects.count()
            self.stdout.write(f"📊 Total Topics in Library: {total_topics}")

        self.stdout.write(self.style.SUCCESS("🎉 Academics Data Seeding Complete! (Your dashboard remains clean)"))