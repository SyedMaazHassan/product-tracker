# Generated by Django 4.2 on 2024-03-13 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_product_inventory_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='distribution',
            field=models.CharField(blank=True, choices=[('Normal Distribution', 'Normal Distribution'), ('Uniform distribution', 'Uniform distribution'), ('Beta distribution', 'Beta distribution'), ('Gamma distribution', 'Gamma distribution')], max_length=50, null=True, verbose_name='Distribution'),
        ),
    ]
