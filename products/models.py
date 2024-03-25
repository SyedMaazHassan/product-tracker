from django.db import models
from math import sqrt
from django.db.models import Sum
import math
from scipy.stats import norm
from django.utils import timezone
# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver


class Product(models.Model):
    DISTRIBUTION_CHOICES = [
        ('Normal Distribution', 'Normal Distribution'),
        ('Uniform Distribution', 'Uniform Distribution'),
        ('Beta Distribution', 'Beta Distribution'),
        ('Gamma Distribution', 'Gamma Distribution')   
    ]
    product_id = models.CharField(max_length=20, unique=True, verbose_name="Product ID")
    product_name = models.CharField(max_length=100, verbose_name="Product Name")
    policy_name = models.CharField(max_length = 10, null=True, blank=True)
    distribution = models.CharField(max_length=50, verbose_name="Distribution", null=True, blank=True, choices=DISTRIBUTION_CHOICES)
    product_supplier = models.CharField(max_length=100, verbose_name="Product Supplier")
    stock_level = models.CharField(max_length=50, verbose_name="Stock Level", choices=[('Normal', 'Normal'), ('Low', 'Low')])
    inventory_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_all_orders(self):
        return self.order_set.all()

    def get_outstanding_orders(self):
        return self.order_set.filter(status='Awaiting').aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    
    def update_stock_level(self):
        policy_type = self.get_policy()
        if policy_type['key'] == 's-s':
            if self.inventory_level <= policy_type['instance'].minimum_stock_level:
                self.stock_level = "Low"
            else:
                self.stock_level = "Normal"
        # If s, S policy, 
        # if inventory_level <= minimum_stock_level = Low, else normal

        if policy_type['key'] == 't-s':
            if self.inventory_level <= policy_type['instance'].target_level:
                self.stock_level = 'Low'
            else:
                self.stock_level = 'Normal'


        # If T, S Policy
        # if invetory_level <- target_level = Low, else, Normal

        if policy_type['key'] == 'r-q':
            if self.inventory_level <= policy_type['instance'].reorder_point:
                self.stock_level = "Low"
            else:
                self.stock_level = 'Normal'

        # if R, Q policy
        # if inventory_level <= reorder_point = Low, else Normal

    @property
    def policy_key(self):
        return self.get_policy()['key']

    def get_policy(self):
        instance = name = abbr = key = None
        if hasattr(self, 'continuous_review_rq_policy'):
            instance = self.continuous_review_rq_policy
            name = self.continuous_review_rq_policy.name
            abbr = self.continuous_review_rq_policy.abbr
            key = 'r-q'

        elif hasattr(self, 'periodic_review_ts_policy'):

            instance = self.periodic_review_ts_policy
            name = self.periodic_review_ts_policy.name
            abbr = self.periodic_review_ts_policy.abbr
            key = 't-s'

        elif hasattr(self, 'continuous_review_ss_policy'):

            instance = self.continuous_review_ss_policy
            name = self.continuous_review_ss_policy.name
            abbr = self.continuous_review_ss_policy.abbr
            key = 's-s'

        print(abbr, "YES")

        return {
            'instance': instance,
            'name': name,
            'abbr': abbr,
            'key': key
        }



    def __str__(self):
        return f'{self.product_name} ({self.policy_name} Policy)'


class Notification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length = 255)
    body = models.TextField()
    is_new = models.BooleanField(default = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)


class InvetorylevelUpdate(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    is_stockout = models.BooleanField()
    created_at = models.DateField(default=timezone.now)

    def __str__(self):
        return f'{self.product}, {self.quantity}, Stockout = {self.is_stockout}'

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length = 15, default='Awaiting', null=True, blank=True, choices=[('Awaiting', 'Awaiting'), ('Completed', 'Completed')])
    estimated_days = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def get_lead_time(self):
        if self.completed_at:
            lead_time = self.completed_at - self.created_at
            days = lead_time.days   # Lead time in days
            return max(days, 1)
        else:
            return 0 
        
    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f'OrderID {self.id}'

class ContinuousReviewRQPolicy(models.Model):
    name = models.CharField(max_length=100, default="Continuous review policy (R, Q)", editable=False)
    abbr = models.CharField(max_length=100, default="R, Q", editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='continuous_review_rq_policy')
    setup_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Setup Cost (S)")
    holding_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Holding Cost (H)")
    order_lead_time = models.IntegerField(verbose_name="Order Lead Time (LT)")
    average_demand = models.IntegerField(verbose_name="Average Demand (µd)")
    daily_demand = models.IntegerField(verbose_name="Daily Demand")
    number_of_days_in_year = models.IntegerField(verbose_name="Number of Days in Year (D)")
    average_lead_time = models.IntegerField(verbose_name="Average Lead Time")
    is_constant_lead_time = models.BooleanField(default=False)
    is_constant_demand = models.BooleanField(default=False)

    normal_distribution_inputs = models.JSONField(null=True, blank=True)
    uniform_distribution_inputs = models.JSONField(null=True, blank=True)
    beta_distribution_inputs = models.JSONField(null=True, blank=True)
    gamma_distribution_inputs = models.JSONField(null=True, blank=True) 

    eoq = models.IntegerField(blank=True, null=True, verbose_name="Economic Order Quantity (EOQ)")
    reorder_point = models.IntegerField(blank=True, null=True, verbose_name="Reorder Point (ROP)")
    safety_stock = models.IntegerField(blank=True, null=True, verbose_name="Safety Stock")

    def calculate_eoq(self):
        D = self.number_of_days_in_year * self.daily_demand
        H = self.holding_cost
        S = self.setup_cost
        eoq = math.sqrt((2 * D * S) / H)
        return eoq

    def calculate_rop_in_normal(self):
        service_level = self.normal_distribution_inputs['service_level']
        z_alpha = norm.ppf(service_level/100)

        if not self.is_constant_lead_time and not self.is_constant_demand:
            std_LT = self.normal_distribution_inputs['std_dev_lead_time']
            safety_stock = z_alpha * std_LT
            
            LT = self.order_lead_time
            µd = self.average_demand
            rop = (µd * LT) + safety_stock

        if self.is_constant_demand and not self.is_constant_lead_time:
            std_LT = self.normal_distribution_inputs['std_dev_lead_time']
            safety_stock = z_alpha * std_LT

            rop = (self.daily_demand * self.average_lead_time) + (self.daily_demand * safety_stock)

        if not self.is_constant_demand and self.is_constant_lead_time:
            std_d = self.normal_distribution_inputs['std_dev_daily_demand']
            LT = self.order_lead_time
            sqrt_LT = math.sqrt(LT)
            safety_stock = z_alpha * std_d * sqrt_LT

            µd = self.average_demand

            rop = (µd * LT) + safety_stock

        if self.is_constant_demand and self.is_constant_lead_time:
            std_LT = self.normal_distribution_inputs['std_dev_lead_time']
            safety_stock = z_alpha * std_LT
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop
        

    def calculate_rop_in_uniform(self):
        print("Calculating RQ...")
        µd = self.average_demand
        LT = self.order_lead_time
        b = self.uniform_distribution_inputs['upper_bound']
        a = self.uniform_distribution_inputs['lower_bound']
        safety_stock = (b - a)/2

        if not self.is_constant_lead_time and not self.is_constant_demand:
            rop = (µd * LT) + safety_stock

        if self.is_constant_demand and not self.is_constant_lead_time:             
            rop = (self.daily_demand * self.average_lead_time) + (self.daily_demand * safety_stock)

        if not self.is_constant_demand and self.is_constant_lead_time:
            rop = (µd * LT) + safety_stock

        if self.is_constant_demand and self.is_constant_lead_time:
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop



    def calculate_rop_in_beta(self):
        print("Calculating RQ...")

        quantile = 0.95
        µd = self.average_demand
        LT = self.order_lead_time
        alpha = self.beta_distribution_inputs['alpha']
        beta = self.beta_distribution_inputs['beta']
        B_alpha = norm.ppf(quantile, alpha/100, beta/100)
        std_LT = self.beta_distribution_inputs['std_dev_lead_time']
        std_d = self.beta_distribution_inputs['std_dev_daily_demand']
        sqrt_LT = math.sqrt(LT)
        safety_stock = std_LT

        if not self.is_constant_lead_time and not self.is_constant_demand:
            rop = (µd * LT) + (B_alpha * safety_stock)

        if self.is_constant_demand and not self.is_constant_lead_time:
            rop = (self.daily_demand * self.average_lead_time) + (self.daily_demand * B_alpha * safety_stock)

        if not self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = B_alpha * std_d * sqrt_LT
            rop = (µd * LT) + safety_stock

        if self.is_constant_demand and self.is_constant_lead_time:
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop

    def calculate_rop_in_gamma(self):
        Q = 0.95
        alpha = self.gamma_distribution_inputs['alpha']
        beta = self.gamma_distribution_inputs['beta']
        Q_alpha = norm.ppf(alpha/100, beta/100, Q)
        µd = self.average_demand
        LT = self.order_lead_time
        safety_stock = Q_alpha

        if not self.is_constant_demand and not self.is_constant_lead_time:
            rop = (µd * LT) + Q_alpha

        if self.is_constant_demand and not self.is_constant_lead_time:
            rop = (self.daily_demand * self.average_lead_time) + (self.daily_demand * Q_alpha)

        if not self.is_constant_demand and self.is_constant_lead_time:
            rop = (µd * LT) + Q_alpha

        if self.is_constant_demand and self.is_constant_lead_time:
            rop = (self.daily_demand * self.order_lead_time)

        return safety_stock, rop

    def calculate(self):
        print("Calculating RQ...")
        self.eoq = round(self.calculate_eoq(), 2)
        safety_stock = reorder_point = None
        if self.product.distribution == 'Normal Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_normal()
        if self.product.distribution == 'Uniform Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_uniform()
        if self.product.distribution == 'Beta Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_beta()
        if self.product.distribution == 'Gamma Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_gamma()
        self.safety_stock = round(safety_stock, 2)
        self.reorder_point = round(reorder_point, 2)
        self.save()


class PeriodicReviewTSPolicy(models.Model):
    name = models.CharField(max_length=100, default="Periodic review policy (T, S)", editable=False)
    abbr = models.CharField(max_length=100, default="T, S", editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='periodic_review_ts_policy')
    inventory_review_time = models.IntegerField(verbose_name="Inventory Review Time")
    target_level = models.IntegerField(verbose_name="Target Level")
    order_quantity = models.IntegerField(blank=True, null=True, verbose_name="Order Quantity")


    def calculate(self):
        S = self.target_level
        I = self.product.inventory_level
        O = self.product.get_outstanding_orders()
        Q=S-I+O
        self.order_quantity = round(Q, 2)
        self.save()
    

class ContinuousReviewSSPolicy(models.Model):
    name = models.CharField(max_length=100, default="Continuous review policy (s, S)", editable=False)
    abbr = models.CharField(max_length=100, default="s, S", editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='continuous_review_ss_policy')
    maximum_stock_level = models.IntegerField(verbose_name="Maximum Stock Level")
    minimum_stock_level = models.IntegerField(verbose_name="Minimum Stock Level")
    order_quantity = models.IntegerField(blank=True, null=True, verbose_name="Order Quantity (Q)")

    def calculate(self):
        S = self.maximum_stock_level
        I = self.product.inventory_level
        O = self.product.get_outstanding_orders()
        Q=S-I+O
        self.order_quantity = round(Q, 2)
        self.save()



