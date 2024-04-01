from django.db import models
from math import sqrt
from django.db.models import Sum
import math
from scipy.stats import norm, beta, gamma
from django.utils import timezone
import numpy as np
import math
# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver

class Product(models.Model):
    # Choices for distribution types
    DISTRIBUTION_CHOICES = [
        ('Normal Distribution', 'Normal Distribution'),
        ('Uniform Distribution', 'Uniform Distribution'),
        ('Beta Distribution', 'Beta Distribution'),
        ('Gamma Distribution', 'Gamma Distribution')   
    ]

    # Model fields
    product_id = models.CharField(max_length=20, unique=True, verbose_name="Product ID")
    product_name = models.CharField(max_length=100, verbose_name="Product Name")
    policy_name = models.CharField(max_length=10, null=True, blank=True)
    distribution = models.CharField(max_length=50, verbose_name="Distribution", null=True, blank=True, choices=DISTRIBUTION_CHOICES)
    product_supplier = models.CharField(max_length=100, verbose_name="Product Supplier")
    stock_level = models.CharField(max_length=50, verbose_name="Stock Level", choices=[('Normal', 'Normal'), ('Low', 'Low')])
    inventory_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Method to get all orders associated with this product
    def get_all_orders(self):
        return self.order_set.all()

    # Method to get quantities of all orders associated with this product
    def get_all_orders_quantities(self):
        all_orders = self.get_all_orders()
        all_orders = all_orders.values_list('quantity', flat=True)
        all_orders = list(all_orders)
        return all_orders

    # Method to get total outstanding orders quantity for this product
    def get_outstanding_orders(self):
        return self.order_set.filter(status='Awaiting').aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Method to update stock level based on policy
    def update_stock_level(self):
        policy_type = self.get_policy()

        # Update stock level based on policy type
        if policy_type['key'] == 's-s':
            if self.inventory_level <= policy_type['instance'].minimum_stock_level:
                self.stock_level = "Low"
            else:
                self.stock_level = "Normal"

        if policy_type['key'] == 't-s':
            if self.inventory_level <= policy_type['instance'].target_level:
                self.stock_level = 'Low'
            else:
                self.stock_level = 'Normal'

        if policy_type['key'] == 'r-q':
            if self.inventory_level <= policy_type['instance'].reorder_point:
                self.stock_level = "Low"
            else:
                self.stock_level = 'Normal'

    # Property to get the key of the policy associated with this product
    @property
    def policy_key(self):
        return self.get_policy()['key']

    # Method to get the policy associated with this product
    def get_policy(self):
        instance = name = abbr = key = None

        # Check if continuous review, reorder quantity policy is associated
        if hasattr(self, 'continuous_review_rq_policy'):
            instance = self.continuous_review_rq_policy
            name = self.continuous_review_rq_policy.name
            abbr = self.continuous_review_rq_policy.abbr
            key = 'r-q'

        # Check if periodic review, target stock policy is associated
        elif hasattr(self, 'periodic_review_ts_policy'):
            instance = self.periodic_review_ts_policy
            name = self.periodic_review_ts_policy.name
            abbr = self.periodic_review_ts_policy.abbr
            key = 't-s'

        # Check if continuous review, static stock policy is associated
        elif hasattr(self, 'continuous_review_ss_policy'):
            instance = self.continuous_review_ss_policy
            name = self.continuous_review_ss_policy.name
            abbr = self.continuous_review_ss_policy.abbr
            key = 's-s'

        print(abbr, "YES")  # Debugging line

        return {
            'instance': instance,
            'name': name,
            'abbr': abbr,
            'key': key
        }

    # Method to represent the product instance as a string
    def __str__(self):
        # Format the policy name for representation
        policy = "S, s" if self.policy_name == 's, S' else self.policy_name
        return f'{self.product_name} ({policy} Policy)'


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
    # model fields
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=15, default='Awaiting', null=True, blank=True, choices=[('Awaiting', 'Awaiting'), ('Completed', 'Completed')])
    estimated_days = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Method to calculate the lead time for the order
    def get_lead_time(self):
        if self.completed_at:
            lead_time = self.completed_at - self.created_at
            days = lead_time.days   # Lead time in days
            return max(days, 1)  # Ensuring lead time is at least 1 day
        else:
            return 0  # Return 0 if the order has not been completed

    # Meta class for ordering the instances based on creation time
    class Meta:
        ordering = ('-created_at',)

    # String representation of the order instance
    def __str__(self):
        return f'OrderID {self.id}'


class ContinuousReviewRQPolicy(models.Model):
    # Model representing a continuous review policy with reorder quantity calculation
    # name: Name of the policy
    # abbr: Abbreviation of the policy
    # product: The product associated with this policy
    # order_lead_time: Lead time for ordering
    # average_demand: Average demand for the product
    # daily_demand: Daily demand for the product
    # is_constant_lead_time: Boolean indicating if lead time is constant
    # is_constant_demand: Boolean indicating if demand is constant
    # normal_distribution_inputs: Inputs for normal distribution
    # uniform_distribution_inputs: Inputs for uniform distribution
    # beta_distribution_inputs: Inputs for beta distribution
    # gamma_distribution_inputs: Inputs for gamma distribution
    # eoq: Economic Order Quantity
    # reorder_point: Reorder point
    # safety_stock: Safety stock

    name = models.CharField(max_length=100, default="Continuous review policy (R, Q)", editable=False)
    abbr = models.CharField(max_length=100, default="R, Q", editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='continuous_review_rq_policy')
    order_lead_time = models.IntegerField(verbose_name="Order Lead Time (LT)")
    average_demand = models.IntegerField(verbose_name="Average Demand (µd)")
    daily_demand = models.IntegerField(verbose_name="Daily Demand")
    is_constant_lead_time = models.BooleanField(default=False)
    is_constant_demand = models.BooleanField(default=False)

    normal_distribution_inputs = models.JSONField(null=True, blank=True)
    uniform_distribution_inputs = models.JSONField(null=True, blank=True)
    beta_distribution_inputs = models.JSONField(null=True, blank=True)
    gamma_distribution_inputs = models.JSONField(null=True, blank=True) 

    eoq = models.IntegerField(blank=True, null=True, verbose_name="Order Quantity")
    reorder_point = models.IntegerField(blank=True, null=True, verbose_name="Reorder Point (ROP)")
    safety_stock = models.IntegerField(blank=True, null=True, verbose_name="Safety Stock")

    # Method to calculate Economic Order Quantity (EOQ)
    def calculate_oq(self):
        O = self.product.get_outstanding_orders()
        # EOQ formula calculation
        oq = (self.daily_demand * self.order_lead_time) + self.safety_stock - O
        return oq

    # Method to calculate Reorder Point (ROP) using Normal Distribution
    def calculate_rop_in_normal(self):
        service_level = self.normal_distribution_inputs['service_level']
        z_alpha = norm.ppf(service_level)
        z_alpha = round(z_alpha, 2)

        # If lead time and demand are both variable
        if not self.is_constant_lead_time and not self.is_constant_demand:
            std_LT = self.normal_disatribution_inputs['std_dev_lead_time']
            safety_stock = z_alpha * std_LT
            
            LT = self.order_lead_time
            µd = self.average_demand
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If demand is constant but lead time is variable
        if self.is_constant_demand and not self.is_constant_lead_time:
            std_LT = self.normal_distribution_inputs['std_dev_lead_time']
            safety_stock = math.ceil(z_alpha * std_LT * self.daily_demand)
            safety_stock = safety_stock
            # ROP calculation
            rop = (self.daily_demand * self.order_lead_time) + (safety_stock)

        # If demand is variable but lead time is constant
        if not self.is_constant_demand and self.is_constant_lead_time:
            std_d = self.normal_distribution_inputs['std_dev_daily_demand']
            LT = self.order_lead_time
            sqrt_LT = math.sqrt(LT)
            safety_stock = z_alpha * std_d * sqrt_LT
            safety_stock = safety_stock
            µd = self.average_demand
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If both demand and lead time are constant
        if self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = 0
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop
        
    # Method to calculate Reorder Point (ROP) using Uniform Distribution
    def calculate_rop_in_uniform(self):
        print("Calculating RQ...")
        µd = self.average_demand
        LT = self.order_lead_time
        b = self.uniform_distribution_inputs['upper_bound']
        a = self.uniform_distribution_inputs['lower_bound']
        safety_stock = (b - a)/2
        safety_stock = math.ceil(safety_stock)

        # If both lead time and demand are variable
        if not self.is_constant_lead_time and not self.is_constant_demand:
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If demand is constant but lead time is variable
        if self.is_constant_demand and not self.is_constant_lead_time: 
            safety_stock = self.daily_demand * safety_stock
            # ROP calculation
            rop = (self.daily_demand * self.order_lead_time) + (safety_stock)

        # If demand is variable but lead time is constant
        if not self.is_constant_demand and self.is_constant_lead_time:
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If both demand and lead time are constant
        if self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = 0
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop

    # Method to calculate Reorder Point (ROP) using Beta Distribution
    def calculate_rop_in_beta(self):
        quantile = self.beta_distribution_inputs['service_level']
        µd = self.average_demand
        LT = self.order_lead_time
        alpha = self.beta_distribution_inputs['alpha']
        B = self.beta_distribution_inputs['beta']
        B_alpha = beta.ppf(quantile, alpha, B)
        std_LT = self.beta_distribution_inputs['std_dev_lead_time']
        std_d = self.beta_distribution_inputs['std_dev_daily_demand']
        sqrt_LT = math.sqrt(LT)
        safety_stock = 0

        # If both lead time and demand are variable
        if not self.is_constant_lead_time and not self.is_constant_demand:
            safety_stock = B_alpha * std_LT
            safety_stock = math.ceil(safety_stock)
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If demand is constant but lead time is variable
        if self.is_constant_demand and not self.is_constant_lead_time:
            safety_stock = self.daily_demand * B_alpha * std_LT
            safety_stock = math.ceil(safety_stock)
            # ROP calculation
            rop = (self.daily_demand * self.order_lead_time) + safety_stock

        # If demand is variable but lead time is constant
        if not self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = B_alpha * std_d * sqrt_LT
            safety_stock = math.ceil(safety_stock)
            # ROP calculation
            rop = (µd * LT) + safety_stock

        # If both demand and lead time are constant
        if self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = 0
            rop = self.daily_demand * self.order_lead_time

        return safety_stock, rop

    # Method to calculate Reorder Point (ROP) using Gamma Distribution
    def calculate_rop_in_gamma(self):
        all_orders_quantities = self.product.get_all_orders_quantities()
        length_of_order_quantities = len(all_orders_quantities)

        Q = self.gamma_distribution_inputs['service_level']
        alpha = self.gamma_distribution_inputs['alpha']
        beta = self.gamma_distribution_inputs['beta']
        
        # If there are existing orders in the database
        if length_of_order_quantities > 0:
            Q_alpha = np.quantile(all_orders_quantities, Q)
        else:
            Q_alpha = gamma.ppf(Q, alpha, scale=beta)

        Q_alpha = math.ceil(Q_alpha)
        µd = self.average_demand
        LT = self.order_lead_time
        safety_stock = Q_alpha
        safety_stock = math.ceil(safety_stock)

        # If both demand and lead time are variable
        if not self.is_constant_demand and not self.is_constant_lead_time:
            # ROP calculation
            rop = (µd * LT) + Q_alpha

        # If demand is constant but lead time is variable
        if self.is_constant_demand and not self.is_constant_lead_time:
            safety_stock = Q_alpha * self.daily_demand
            # ROP calculation
            rop = (self.daily_demand * self.order_lead_time) + (safety_stock)

        # If demand is variable but lead time is constant
        if not self.is_constant_demand and self.is_constant_lead_time:
            # ROP calculation
            rop = (µd * LT) + Q_alpha

        # If both demand and lead time are constant
        if self.is_constant_demand and self.is_constant_lead_time:
            safety_stock = 0
            rop = (self.daily_demand * self.order_lead_time)

        return safety_stock, rop

    # Method to calculate reorder quantity and reorder point
    def calculate(self):
        print("Calculating RQ...")

        safety_stock = reorder_point = None
        # Determine the distribution type and calculate ROP accordingly
        if self.product.distribution == 'Normal Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_normal()
        if self.product.distribution == 'Uniform Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_uniform()
        if self.product.distribution == 'Beta Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_beta()
        if self.product.distribution == 'Gamma Distribution':
            safety_stock, reorder_point = self.calculate_rop_in_gamma()
        
        # Round safety stock and reorder point to 2 decimal places
        self.safety_stock = round(safety_stock, 2)
        self.reorder_point = round(reorder_point, 2)
        
        # Calculate and round EOQ
        self.eoq = round(self.calculate_oq(), 2)

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
        Q=S-I-O
        Q = max(Q, 0)
        self.order_quantity = round(Q, 2)
        self.save()
    

class ContinuousReviewSSPolicy(models.Model):
    name = models.CharField(max_length=100, default="Continuous review policy (s, S)", editable=False)
    abbr = models.CharField(max_length=100, default="s, S", editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='continuous_review_ss_policy')
    maximum_stock_level = models.IntegerField(verbose_name="Maximum Stock Level (S)")
    minimum_stock_level = models.IntegerField(verbose_name="Minimum Stock Level (s)")
    order_quantity = models.IntegerField(blank=True, null=True, verbose_name="Order Quantity (Q)")

    def calculate(self):
        S = self.maximum_stock_level
        I = self.product.inventory_level
        O = self.product.get_outstanding_orders()
        
        Q=S-I-O
        Q = max(Q, 0)
        self.order_quantity = round(Q, 2)
        self.save()



