# Generated by Django 5.1.3 on 2024-11-13 18:48

from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    username = "admin"
    superuser_email = "admin@tenis.upm.es"
    superuser_password = "admin"

    if not User.objects.filter(email=superuser_email).exists():
        User.objects.create_superuser(username=username, email=superuser_email, password=superuser_password)
        print(f"Superuser {superuser_email} created successfully.")
    else:
        print(f"Superuser {superuser_email} already exists.")

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
