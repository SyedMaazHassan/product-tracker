# Generated by Django 4.2 on 2024-03-29 16:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_alter_notification_options_alter_order_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ('-created_at',)},
        ),
    ]
