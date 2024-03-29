from django import forms
from .models import Order, Product, ContinuousReviewRQPolicy, PeriodicReviewTSPolicy, ContinuousReviewSSPolicy

class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', None)
        super(ProductForm, self).__init__(*args, **kwargs)
    
    def clean_distribution(self):
        distribution = self.cleaned_data.get('distribution')
        policy_name = None
        if self.context:
            policy_name = self.context.get('policy_name')

        if policy_name == 'r-q' and not distribution:
            raise forms.ValidationError('This field is required.')
        return distribution

    class Meta:
        model = Product
        exclude = ['policy_name', 'stock_level', 'created_at']


class ContinuousReviewRQPolicyForm(forms.ModelForm):
    class Meta:
        model = ContinuousReviewRQPolicy
        exclude = ['normal_distribution_inputs', 'uniform_distribution_inputs', 'beta_distribution_inputs', 'gamma_distribution_inputs', 'eoq', 'reorder_point', 'safety_stock', 'product']

class PeriodicReviewTSPolicyForm(forms.ModelForm):
    class Meta:
        model = PeriodicReviewTSPolicy
        exclude = ['order_quantity', 'product']

class ContinuousReviewSSPolicyForm(forms.ModelForm):
    class Meta:
        model = ContinuousReviewSSPolicy
        exclude = ['order_quantity', 'product']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['completed_at']


class NormalDistributionForm(forms.Form):
    service_level = forms.FloatField(label='Service Level', min_value=0, max_value=1)
    std_dev_lead_time = forms.FloatField(label='Standard Deviation of Demand during Lead Time (σLT)')
    std_dev_daily_demand = forms.FloatField(label='Standard Deviation of Daily Demand (σd)')

class UniformDistributionForm(forms.Form):
    lower_bound = forms.FloatField(label='Lower Bound (a)')
    upper_bound = forms.FloatField(label='Upper Bound (b)')

class BetaDistributionForm(forms.Form):
    service_level = forms.FloatField(label='Service Level', min_value=0, max_value=1)
    beta = forms.FloatField(label='Beta (β)', min_value=0, max_value=1)
    alpha = forms.FloatField(label='Alpha (α)', min_value=0, max_value=1)
    std_dev_lead_time = forms.FloatField(label='Standard Deviation of Demand during Lead Time (σLT)')
    std_dev_daily_demand = forms.FloatField(label='Standard Deviation of Daily Demand (σd)')


class GammaDistributionForm(forms.Form):
    service_level = forms.FloatField(label='Service Level', min_value=0, max_value=1)
    beta = forms.FloatField(label='Beta (β)', min_value=0, max_value=1)
    alpha = forms.FloatField(label='Alpha (α)', min_value=0, max_value=1)