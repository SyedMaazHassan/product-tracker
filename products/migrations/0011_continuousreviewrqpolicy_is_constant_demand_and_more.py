# Generated by Django 4.2 on 2024-03-15 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_alter_product_distribution'),
    ]

    operations = [
        migrations.AddField(
            model_name='continuousreviewrqpolicy',
            name='is_constant_demand',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='continuousreviewrqpolicy',
            name='is_constant_lead_time',
            field=models.BooleanField(default=False),
        ),
    ]
