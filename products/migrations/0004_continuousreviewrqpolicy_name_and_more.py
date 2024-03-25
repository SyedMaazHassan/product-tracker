# Generated by Django 4.2 on 2024-03-12 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_continuousreviewrqpolicy_alpha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='continuousreviewrqpolicy',
            name='name',
            field=models.CharField(default='Continuous review policy (R, Q)', editable=False, max_length=100),
        ),
        migrations.AddField(
            model_name='continuousreviewsspolicy',
            name='name',
            field=models.CharField(default='Continuous review policy (s, S)', editable=False, max_length=100),
        ),
        migrations.AddField(
            model_name='periodicreviewtspolicy',
            name='name',
            field=models.CharField(default='Periodic review policy (T, S)', editable=False, max_length=100),
        ),
    ]