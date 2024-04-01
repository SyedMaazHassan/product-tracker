from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from django.db import transaction
import random
from django.db.models import Q
from faker import Faker
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from django.utils import timezone
from random import randint
import calendar
import json
from calendar import monthrange

# Create your views here.


def create_fake_orders(num_orders):
    fake = Faker()
    orders = []
    statuses = ['Awaiting', 'Completed']

    for _ in range(num_orders):
        product = random.choice(Product.objects.all())
        quantity = random.randint(1, 100)
        status = random.choice(statuses)
        estimated_days = random.randint(1, 30)  # Adjust range as needed
        created_at = fake.date_time_between(start_date="-1y", end_date="now", tzinfo=timezone.get_current_timezone())

        order = Order(product=product, quantity=quantity, status=status, estimated_days=estimated_days, created_at=created_at)
        orders.append(order)

    Order.objects.bulk_create(orders)


@login_required
def search_products(request):
    query = request.GET.get('query')
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(product_name__icontains=query) | Q(product_id__icontains=query) | Q(product_supplier__icontains=query)
        )

    return render(request, "search-products.html", {'products': products, 'query': query})


def get_inventory_levels_chart():
# Calculate the start date for the last 12 months
    end_date = timezone.now()  # Current date and time
    start_date = end_date - timedelta(days=365)
    labels = []
    data = {
        'S, s': [],
        'R, Q': [],
        'T, S': []
    }
    color_mapping = {
        'R, Q': 'rgba(17, 141, 255)',  # Darker color for 'R, Q' policy
        'S, s': 'rgba(18, 35, 158)',   # Darker color for 's, S' policy
        'T, S': 'rgba(230, 108, 55)'    # Darker color for 'T, S' policy
    }

    for i in range(13):
        month = start_date.month
        year = start_date.year
        month_name = calendar.month_abbr[month]
        products_per_month = Product.objects.filter(created_at__month=month, created_at__year=year).values('policy_name').annotate(
            total_inventory=Sum('inventory_level')
        )
        for entry in products_per_month:
            policy_name = entry['policy_name']
            new_policy = policy_name if policy_name != "s, S" else "S, s"
            total_inventory = entry['total_inventory']
            data[new_policy].append(total_inventory)
        labels.append(f'{month_name} {year}')
        start_date = start_date + timedelta(days=30)

    dataset = {}
    for key, value in data.items():
        dataset[key] = {
            'label': key,
            'data': value,
            'backgroundColor': color_mapping.get(key, 'rgba(153, 102, 255, 0.2)'),
            'borderColor': color_mapping.get(key, 'rgba(153, 102, 255, 1)'),
            'borderWidth': 4,
            'lineTension': 0.3
        }

    ready_data = {
        'labels': labels,
        'datasets': list(dataset.values())
    }
    return json.dumps(ready_data)


def get_orders_chart():
    rq_order = Order.objects.filter(product__policy_name='R, Q').count()
    ss_order = Order.objects.filter(product__policy_name='s, S').count()
    ts_order = Order.objects.filter(product__policy_name='T, S').count()
    labels = ['S, s', 'R, Q', 'T, S']
    orders_qty = [ss_order, rq_order, ts_order]
    data = {
        'labels': labels,
        'datasets': [{
            'label': 'Total Orders by policy',
            'data': orders_qty,
            'backgroundColor': [
                'rgba(18, 35, 158)',
                'rgba(17, 141, 255)',
                'rgba(230, 108, 55)'
            ],
            'hoverOffset': 4
        }]
    }
    return json.dumps(data)


def generate_estimated_days_data(product_id):
    # Get the current date
    current_date = datetime.now()

    # Initialize lists
    month_list = []
    estimated_days_list = []

    all_orders = Order.objects.filter(status="Completed", product_id = product_id)
    all_order_names = []
    all_order_estimated_days = list(all_orders.values_list('estimated_days', flat=True))
    all_lead_times = []
    for order in all_orders:
        all_order_names.append(str(order))
        all_lead_times.append(order.get_lead_time())

    # Construct the data structure for the line chart
    estimated_days_data = {
        'labels': all_order_names,
        'datasets': [
            {
                'type': 'line',
                'label': 'Order Lead Time (in days)',
                'data': all_lead_times,
                'backgroundColor': 'rgba(113, 201, 245)',
                'borderColor': 'rgba(113, 201, 245)',
                'borderWidth': 4,
                'lineTension': 0.3
            },
        ]
    }

    return json.dumps(estimated_days_data)


def get_product_chart():
    ts = PeriodicReviewTSPolicy.objects.all().count()
    ss = ContinuousReviewSSPolicy.objects.all().count()
    rq = ContinuousReviewRQPolicy.objects.all().count()
    labels = ['S, s policy', 'R, Q policy', 'T, S policy']
    total_products = [ss, rq, ts]
    data = {
        'labels': labels,
        'datasets': [{
            'label': 'Total Products',
            'data': total_products,
            'backgroundColor': [
                'rgba(18, 35, 158)',
                'rgba(17, 141, 255)',
                'rgba(230, 108, 55)'
            ],
            'borderColor': [
                'rgba(18, 35, 158)',
                'rgba(17, 141, 255)',
                'rgba(230, 108, 55)'
            ],
            'borderWidth': 1
        }]
    }
    print(data)
    return json.dumps(data)


def generate_inventory_data(product_id):
    # Get the current date
    current_date = datetime.now()
    
    # Initialize lists
    month_list = []
    inventory_level_quantity_list = []
    order_qty = []
    all_products_orders = Order.objects.filter(product_id = product_id)

    # Calculate the past 12 months (including the current month)
    for i in range(11, -1, -1):
        # Calculate the year and month for the current iteration
        year = current_date.year - (i // 12)
        month = current_date.month - (i % 12)
        if month <= 0:
            month += 12
            year -= 1
        
        # Calculate the first and last day of the month
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, monthrange(year, month)[1])
        
        month_year = first_day.strftime('%b %Y')
        month_list.append(month_year)
        
        # Aggregate inventory level quantities for the current month
        inventory_level_quantity = InvetorylevelUpdate.objects.filter(
            product_id=product_id,
            created_at__gte=first_day,
            created_at__lte=last_day
        ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        
        # Assuming 'all_products_orders' is your queryset containing all orders for all products
        order_qty_in_month_total = all_products_orders.filter(
            created_at__gte=first_day,
            created_at__lte=last_day
        ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        
        inventory_level_quantity_list.append(inventory_level_quantity)
        order_qty.append(order_qty_in_month_total)

     # Construct the product inventory data structure
    product_inventory_data = {
        'labels': month_list,
        'datasets': [
            {
                'type': 'bar',
                'label': 'Inventory Level',
                'data': inventory_level_quantity_list,
                'backgroundColor': 'rgba(113, 201, 245, 0.4)',
                'borderColor': 'rgba(113, 201, 245, 0.4)',
                'borderWidth': 1
            },
            {
                'type': 'line',
                'label': 'Total Ordered Quantity',
                'data': order_qty,
                'backgroundColor': 'rgba(113, 201, 245)',
                'borderColor': 'rgba(113, 201, 245)',
                'borderWidth': 4,
                'lineTension': 0.3
            },
            
        ]
    }
    
    return json.dumps(product_inventory_data)


def generate_stockout_data(product_id):
    # Get the current date
    current_date = datetime.now()
    
    # Initialize lists
    month_list = []
    stockout_count_list = []
    
    # Calculate the past 12 months (including the current month)
    for i in range(11, -1, -1):
        # Calculate the year and month for the current iteration
        year = current_date.year - (i // 12)
        month = current_date.month - (i % 12)
        if month <= 0:
            month += 12
            year -= 1
        
        # Calculate the first and last day of the month
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, monthrange(year, month)[1])
        
        month_year = first_day.strftime('%b %Y')
        month_list.append(month_year)
        
        # Count stockouts for the current month
        stockout_count = InvetorylevelUpdate.objects.filter(
            product_id=product_id,
            created_at__gte=first_day,
            created_at__lte=last_day,
            is_stockout=True
        ).count()
        
        stockout_count_list.append(stockout_count)
    
     # Construct the product stockout data structure
    product_stockout_data = {
        'labels': month_list,
        'datasets': [{
            'label': 'Stockout Count',
            'data': stockout_count_list,
            'backgroundColor': 'rgba(113, 201, 245)',
            'borderColor': 'rgba(113, 201, 245)',
            'borderWidth': 4,
            'lineTension': 0.3
        }]
    }
    
    return json.dumps(product_stockout_data)



def generate_order_data(product_id):
    # Get the counts of orders for each status for the given product
    product_order = Order.objects.filter(product_id=product_id)
    
    # Initialize lists for labels and data
    labels = {
        'Awaiting': product_order.filter(status = 'Awaiting').count(),
        'Completed': product_order.filter(status = 'Completed').count()
    }
    

    # Construct the data structure for the pie chart
    order_data = {
        'labels': list(labels.keys()),
        'datasets': [{
            'label': ['Order Quantity by Status'],
            'data': list(labels.values()),
            'backgroundColor': [
                'rgba(113, 201, 245, 0.4)',
                'rgba(113, 201, 245)'
            ],
            'hoverOffset': 4
        }]
    }
    
    return json.dumps(order_data)


@login_required
def dashboard_view(request):
    product_charts = {}
    selected_product = request.GET.get('product')
    if selected_product:
        selected_product = Product.objects.filter(id = selected_product).first()
        if not selected_product:
            messages.error(request, "Invalid product")
            return redirect("products:dashboard")
        

        # Get inventory levels by months
        product_inventory = generate_inventory_data(selected_product.id)
        product_charts['product_inventory'] = product_inventory

        # Get order quantity graph
        order_status = generate_order_data(selected_product.id)
        product_charts['product_order_status'] = order_status

        product_stockout = generate_stockout_data(selected_product.id)
        product_charts['product_stockout'] = product_stockout


        product_order_leadtime = generate_estimated_days_data(selected_product.id)
        product_charts['product_leadtime'] = product_order_leadtime
        print(product_order_leadtime, "=")


    context = {
        'product_charts': product_charts,
        'products': Product.objects.all(),
        'page': 'dashboard',
        'inventory_levels': get_inventory_levels_chart(),
        'orders_chart': get_orders_chart(),
        'products_chart': get_product_chart()
    }
    return render(request, "dashboard.html", context)


@login_required
def all_products_view(request):
    all_products = Product.objects.all()
    # Define the range of dates
    # start_date = datetime(2023, 3, 1)
    # end_date = datetime(2024, 3, 17)

    # Iterate over each product and update created_at
    # for product in all_products:
    #     random_days = randint(0, (end_date - start_date).days)
    #     random_date = start_date + timedelta(days=random_days)
    #     product.created_at = timezone.make_aware(random_date)
    #     product.save()
    # for product in all_products:
    #     product.policy_name = product.get_policy()['abbr']
    #     if not product.policy_name:
    #         product.delete()
    #         continue
    #     product.save()

    ss = ContinuousReviewSSPolicy.objects.all()
    ts = PeriodicReviewTSPolicy.objects.all()
    rq = ContinuousReviewRQPolicy.objects.all()
    # normal = rq.filter(product__distribution = 'Gamma Distribution')
    # for i in range(len(normal)):
    #     s_uniform = normal[i]
    #     if i > 10:
    #         s_uniform.delete()
        
    # print(normal.count())

    # for s_ss in ts:
    #     s_ss.calculate()
        # product = s_ss.product
        # product.inventory_level = product.inventory_level + 1000
        # product.save()
        # s_rq.calculate()
        

    # create_fake_orders(500)
    context = {
        'page': 'products',
        'all_products': all_products,
        'ss': ss,
        'ts': ts,
        'rq': rq
    }
    return render(request, "products.html", context)




@login_required
def add_product_view(request, policy_name):
    policy_dict = {
        's-s': ('Continuous review policy (S, s)', ContinuousReviewSSPolicy, ContinuousReviewSSPolicyForm, 'S, s'),
        't-s': ('Periodic review policy (T, S)', PeriodicReviewTSPolicy, PeriodicReviewTSPolicyForm, 'T, S'),
        'r-q': ('Continuous review policy (R, Q)', ContinuousReviewRQPolicy, ContinuousReviewRQPolicyForm, 'R, Q')
    }

    if policy_name not in policy_dict.keys():
        messages.error(request, "Invalid policy")
        return redirect("products:all-products")

    selected_policy, model_class, form_class, policy_name_type = policy_dict[policy_name]
    normal_distribution_form = uniform_distribution_form = beta_distribution_form = gamma_distribution_form = None

    if request.method == 'POST':
        try:
            with transaction.atomic():
                product_form = ProductForm(request.POST, context={'policy_name': policy_name})
                normal_distribution_form = NormalDistributionForm(request.POST, prefix='normal')
                uniform_distribution_form = UniformDistributionForm(request.POST, prefix='uniform')
                beta_distribution_form = BetaDistributionForm(request.POST, prefix='beta')
                gamma_distribution_form = GammaDistributionForm(request.POST, prefix='gamma')
            
                form = form_class(request.POST)
                if product_form.is_valid() and form.is_valid():
                    product_data = product_form.cleaned_data
                    distribution = product_data.get('distribution')
                    print(product_data)
                    print(distribution)
                    if policy_name == 'r-q':
                        attribute_to_set = None
                        if distribution == 'Normal Distribution':
                            selected_policy_distribution = normal_distribution_form
                            attribute_to_set = 'normal_distribution_inputs'

                        elif distribution == 'Uniform Distribution':
                            selected_policy_distribution = uniform_distribution_form
                            attribute_to_set = 'uniform_distribution_inputs'

                        elif distribution == 'Beta Distribution':
                            selected_policy_distribution = beta_distribution_form
                            attribute_to_set = 'beta_distribution_inputs'

                        else:
                            selected_policy_distribution = gamma_distribution_form
                            attribute_to_set = 'gamma_distribution_inputs'

                        if selected_policy_distribution.is_valid():
                            product = product_form.save()

                            policy_instance = model_class(
                                product=product, **form.cleaned_data
                            )
                            setattr(policy_instance, attribute_to_set, dict(selected_policy_distribution.cleaned_data))
                            policy_instance.calculate()
                            policy_instance.save()
                            
                            product.update_stock_level()
                            product.policy_name = policy_name_type
                            product.save()

                            
                            messages.success(request, "Product added successfully")
                            return redirect("products:all-products")

                    else:
                        product = product_form.save()


                        policy_instance = model_class(product=product, **form.cleaned_data)
                        policy_instance.calculate()
                        policy_instance.save()

                        product.update_stock_level()
                        product.policy_name = policy_name_type
                        product.save()

                        messages.success(request, "Product added successfully")
                        return redirect("products:all-products")
                    
        except Exception as e:
            messages.error(request, str(e))
            return redirect("products:all-products")
        
    else:
        product_form = ProductForm()
        form = form_class()

        normal_distribution_form = NormalDistributionForm(prefix='normal')
        uniform_distribution_form = UniformDistributionForm(prefix='uniform')
        beta_distribution_form = BetaDistributionForm(prefix='beta')
        gamma_distribution_form = GammaDistributionForm(prefix='gamma')


    context = {
        'page': 'products',
        'selected_policy': selected_policy,
        'product_form': product_form,
        'form': form,
        'policy_name': policy_name,
        'normal_distribution_form': normal_distribution_form,
        'uniform_distribution_form': uniform_distribution_form,
        'beta_distribution_form': beta_distribution_form,
        'gamma_distribution_form': gamma_distribution_form
    }
    return render(request, "add-product.html", context)


@login_required
def delete_product_view(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect("products:all-products")

    product.delete()
    messages.success(request, "Product has been deleted")
    return redirect("products:all-products")


@login_required
def edit_product_view(request, policy_name, product_id):
    policy_dict = {
        's-s': ('Continuous review policy (s, S)', ContinuousReviewSSPolicy, ContinuousReviewSSPolicyForm),
        't-s': ('Periodic review policy (T, S)', PeriodicReviewTSPolicy, PeriodicReviewTSPolicyForm),
        'r-q': ('Continuous review policy (R, Q)', ContinuousReviewRQPolicy, ContinuousReviewRQPolicyForm)
    }

    if policy_name not in policy_dict.keys():
        messages.error(request, "Invalid policy")
        return redirect("products:all-products")

    selected_policy, model_class, form_class = policy_dict[policy_name]
    normal_distribution_form = uniform_distribution_form = beta_distribution_form = gamma_distribution_form = None

    # Fetch the product instance
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect("products:all-products")

    if request.method == 'POST':
        product_form = ProductForm(request.POST, instance=product, context={'policy_name': policy_name})
        normal_distribution_form = NormalDistributionForm(request.POST, prefix='normal')
        uniform_distribution_form = UniformDistributionForm(request.POST, prefix='uniform')
        beta_distribution_form = BetaDistributionForm(request.POST, prefix='beta')
        gamma_distribution_form = GammaDistributionForm(request.POST, prefix='gamma')

        form = form_class(request.POST)
        if product_form.is_valid() and form.is_valid():
            product_data = product_form.cleaned_data
            distribution = product_data.get('distribution')
            print(product_data)
            print(distribution)
            if policy_name == 'r-q':
                attribute_to_set = None
                if distribution == 'Normal Distribution':
                    selected_policy_distribution = normal_distribution_form
                    attribute_to_set = 'normal_distribution_inputs'

                elif distribution == 'Uniform Distribution':
                    selected_policy_distribution = uniform_distribution_form
                    attribute_to_set = 'uniform_distribution_inputs'

                elif distribution == 'Beta Distribution':
                    selected_policy_distribution = beta_distribution_form
                    attribute_to_set = 'beta_distribution_inputs'

                else:
                    selected_policy_distribution = gamma_distribution_form
                    attribute_to_set = 'gamma_distribution_inputs'

                if selected_policy_distribution.is_valid():
                    product = product_form.save()

                    policy_instance = model_class.objects.get(product=product)
                    policy_instance.__dict__.update(**form.cleaned_data)
                    setattr(policy_instance, attribute_to_set, dict(selected_policy_distribution.cleaned_data))
                    policy_instance.calculate()
                    policy_instance.save()

                    product.update_stock_level()
                    product.save()

                    messages.success(request, "Product updated successfully")
                    return redirect(
                        "products:edit-product", 
                        policy_name=policy_name, 
                        product_id=product_id
                    )

            else:
                product = product_form.save()

                policy_instance = model_class.objects.get(product=product)
                policy_instance.__dict__.update(**form.cleaned_data)
                policy_instance.calculate()
                policy_instance.save()

                product.update_stock_level()
                product.save()

                messages.success(request, "Product updated successfully")
                return redirect(
                        "products:edit-product", 
                        policy_name=policy_name, 
                        product_id=product_id
                    )
    else:
        product_form = ProductForm(instance=product)
        form = form_class(instance=model_class.objects.get(product=product))

        if hasattr(model_class, 'normal_distribution_inputs'):
            normal_distribution_form = NormalDistributionForm(initial=model_class.objects.get(product=product).normal_distribution_inputs, prefix='normal')
        if hasattr(model_class, 'uniform_distribution_inputs'):
            uniform_distribution_form = UniformDistributionForm(initial=model_class.objects.get(product=product).uniform_distribution_inputs, prefix='uniform')
        if hasattr(model_class, 'beta_distribution_inputs'):
            beta_distribution_form = BetaDistributionForm(initial=model_class.objects.get(product=product).beta_distribution_inputs, prefix='beta')
        if hasattr(model_class, 'gamma_distribution_inputs'):
            gamma_distribution_form = GammaDistributionForm(initial=model_class.objects.get(product=product).gamma_distribution_inputs, prefix='gamma')

    context = {
        'product': product,
        'page': 'products',
        'selected_policy': selected_policy,
        'product_form': product_form,
        'form': form,
        'policy_name': policy_name,
        'normal_distribution_form': normal_distribution_form,
        'uniform_distribution_form': uniform_distribution_form,
        'beta_distribution_form': beta_distribution_form,
        'gamma_distribution_form': gamma_distribution_form
    }
    return render(request, "edit-product.html", context)




# @login_required
# def edit_product_view(request, product_id):
    # try:
    #     product = Product.objects.get(product_id = product_id)
    # except Exception as e:
    #     messages.error(request, str(e))
    #     return redirect('products:all-products')
    
#     selected_policy = product.get_policy()


#     if selected_policy['abbr'] == 'R, Q':
#         policy_name = 'r-q'
#         model_class = ContinuousReviewRQPolicy
#         form_class = ContinuousReviewRQPolicyForm
#     elif selected_policy['abbr'] == 'T, S':
#         policy_name = 't-s'
#         model_class = PeriodicReviewTSPolicy
#         form_class = PeriodicReviewTSPolicyForm
#     else:
#         policy_name = 's-s'
#         model_class = ContinuousReviewSSPolicy
#         form_class = ContinuousReviewSSPolicyForm

#     if request.method == 'POST':
#         product_form = ProductForm(request.POST, instance=product)
#         form = form_class(request.POST, instance=selected_policy['instance'])
#         if product_form.is_valid() and form.is_valid():
#             product = product_form.save(commit=False)
#             product.update_stock_level()
#             product.save()

#             policy = form.save(commit=False)
#             policy.calculate()
#             policy.save()
#             messages.success(request, f"Product {product} edited successfully")
#             return redirect("products:all-products")
#     else:
#         product_form = ProductForm(instance=product)
#         form = form_class(instance=selected_policy['instance'])

#     context = {
#         'page': 'products',
#         'selected_policy': selected_policy,
#         'product_form': product_form,
#         'form': form,
#         'product': product,
#         'policy_name': policy_name
#     }
#     return render(request, "edit-product.html", context)



@login_required
def all_orders_view(request):
    orders = Order.objects.all().order_by("-created_at")
    # completed_orders = orders.filter(status = 'Completed')
    # # Run a loop to add random dates in the completed_at field
    # for order in completed_orders:
    #     print(order)
    #     # Generate a random timedelta between 1 and 30 days
    #     random_days = random.randint(1, 30)
    #     # Add the random timedelta to the created_at datetime
    #     random_completed_at = order.created_at + timedelta(days=random_days)
    #     # Assign the random_completed_at to the completed_at field
    #     order.completed_at = random_completed_at
    #     order.save()

    #     print(order.get_lead_time(), "=")


    policy = request.GET.get('policy')
    product = request.GET.get('product')
    if policy in ['S, s', 'R, Q', 'T, S']:
        products = Product.objects.filter(policy_name = policy)
        orders = orders.filter(product__in = products)
    
    if product and Product.objects.filter(id = product).exists():
        orders = orders.filter(product_id = product)

    context = {
        'page': 'orders',
        'orders': orders,
        'products': Product.objects.all()
    }
    return render(request, "all-orders.html", context)


@login_required
def create_order_view(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, 'Order created successfully!')
            return redirect('products:all-orders')  # Redirect to some success URL
        else:
            print(form.errors)
            messages.error(request, 'Form submission failed. Please correct the errors.')
    else:
        given_product = request.GET.get('product')
        form = OrderForm(initial={'product': given_product})
    return render(request, "create-order.html", {'form': form,'page': 'orders'})



@login_required
def edit_order_view(request, order_id):
    try:
        order = Order.objects.get(id = order_id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('products:all-orders')
    
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order updated successfully!')
            return redirect('products:all-orders')  # Redirect to some success URL
        else:
            messages.error(request, 'Form submission failed. Please correct the errors.')
    else:
        form = OrderForm(instance=order)
    
    return render(request, "edit-order.html", {'form': form, 'page': 'orders'})


@login_required
def delete_order_view(request, order_id):
    try:
        order = Order.objects.get(id = order_id)
        order.delete()
        messages.success(request, "Order deleted successfully!")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('products:all-orders')

@login_required
def all_notifications_view(request):
    notifications = list(Notification.objects.all())
    notifications_to_update = Notification.objects.all()
    for notification in notifications_to_update:
        notification.is_new = False
        notification.save()

    context = {
        'page': 'notifications',
        'notifications': notifications
    }
    return render(request, "all-notifications.html", context)

