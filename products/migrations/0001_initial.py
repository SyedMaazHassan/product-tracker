# Generated by Django 4.2 on 2024-03-12 07:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=20, unique=True, verbose_name='Product ID')),
                ('product_name', models.CharField(max_length=100, verbose_name='Product Name')),
                ('distribution', models.CharField(max_length=50, verbose_name='Distribution')),
                ('product_supplier', models.CharField(max_length=100, verbose_name='Product Supplier')),
                ('stock_level', models.CharField(max_length=50, verbose_name='Stock Level')),
            ],
        ),
        migrations.CreateModel(
            name='PeriodicReviewTSPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inventory_review_time', models.IntegerField(verbose_name='Inventory Review Time')),
                ('target_level', models.IntegerField(verbose_name='Target Level')),
                ('order_quantity', models.IntegerField(blank=True, null=True, verbose_name='Order Quantity')),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='periodic_review_ts_policy', to='products.product')),
            ],
        ),
        migrations.CreateModel(
            name='ContinuousReviewSSPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maximum_stock_level', models.IntegerField(verbose_name='Maximum Stock Level')),
                ('minimum_stock_level', models.IntegerField(verbose_name='Minimum Stock Level')),
                ('order_quantity', models.IntegerField(blank=True, null=True, verbose_name='Order Quantity')),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='continuous_review_ss_policy', to='products.product')),
            ],
        ),
        migrations.CreateModel(
            name='ContinuousReviewRQPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setup_cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Setup Cost')),
                ('holding_cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Holding Cost')),
                ('order_lead_time', models.IntegerField(verbose_name='Order Lead Time')),
                ('daily_demand', models.IntegerField(verbose_name='Daily Demand')),
                ('average_demand', models.IntegerField(verbose_name='Average Demand')),
                ('number_of_days_in_year', models.IntegerField(verbose_name='Number of Days in Year')),
                ('average_lead_time', models.IntegerField(verbose_name='Average Lead Time')),
                ('distribution_type', models.CharField(max_length=50, verbose_name='Distribution Type')),
                ('mean_demand_rate', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Mean Demand Rate')),
                ('desired_service_level', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Desired Service Level')),
                ('std_dev_demand_lead_time', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Standard Deviation of Demand During Lead Time')),
                ('std_dev_daily_demand', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Standard Deviation of Daily Demand')),
                ('upper_bound', models.IntegerField(verbose_name='Upper Bound')),
                ('lower_bound', models.IntegerField(verbose_name='Lower Bound')),
                ('beta', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Beta')),
                ('alpha', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Alpha')),
                ('gamma_distribution_data', models.TextField(blank=True, null=True, verbose_name='Gamma Distribution Data')),
                ('eoq', models.IntegerField(blank=True, null=True, verbose_name='Economic Order Quantity')),
                ('reorder_point', models.IntegerField(blank=True, null=True, verbose_name='Reorder Point')),
                ('safety_stock', models.IntegerField(blank=True, null=True, verbose_name='Safety Stock')),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='continuous_review_rq_policy', to='products.product')),
            ],
        ),
    ]