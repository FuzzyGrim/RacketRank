# Generated by Django 5.1.3 on 2024-11-16 12:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_tournament_registered_participant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='current_round',
            field=models.CharField(choices=[('octavos', 'Octavos de Final'), ('cuartos', 'Cuartos de Final'), ('semifinal', 'Semifinal'), ('final', 'Final')], default='octavos', max_length=255),
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('round', models.CharField(choices=[('octavos', 'Octavos de Final'), ('cuartos', 'Cuartos de Final'), ('semifinal', 'Semifinal'), ('final', 'Final')], max_length=255)),
                ('participant1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant1', to='app.participant')),
                ('participant2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant2', to='app.participant')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.tournament')),
            ],
        ),
    ]
