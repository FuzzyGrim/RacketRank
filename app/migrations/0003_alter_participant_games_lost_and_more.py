# Generated by Django 5.1.3 on 2024-11-17 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_create_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='games_lost',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='participant',
            name='games_won',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='participant',
            name='matches_won',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='participant',
            name='score',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='participant',
            name='sets_won',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='set',
            name='participant1_score',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='set',
            name='participant2_score',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='set',
            name='set_number',
            field=models.PositiveIntegerField(),
        ),
    ]
