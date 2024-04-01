from django.utils import timezone
from datetime import timedelta, datetime
import calendar, json
from django.db.models import Sum, Avg, Count
from .models import *
from django.http import JsonResponse
from calendar import monthrange


def get_products_api(request):
    products = Product.objects.all()
    product_list = []
    for product in products:
        product_list.append(
            {
                'id': product.id,
                'product_name': str(product)
            }
        )
    return JsonResponse(product_list, safe=False)

def get_inventory_levels_chart_api(request):
# Calculate the start date for the last 12 months
    end_date = timezone.now()  # Current date and time
    start_date = end_date - timedelta(days=365)
    total_data = []

    for i in range(13):
        month = start_date.month
        year = start_date.year
        month_name = calendar.month_abbr[month]
        products_per_month = Product.objects.filter(created_at__month=month, created_at__year=year).values('policy_name').annotate(
            total_inventory=Sum('inventory_level')
        )
        for entry in products_per_month:
            policy_name = entry['policy_name']
            total_inventory = entry['total_inventory']
            data_object = {
                'Month': f'{month_name} {year}',
                'Policy': policy_name,
                'InventoryLevel': total_inventory
            }
            total_data.append(data_object)

        start_date = start_date + timedelta(days=30)

    return JsonResponse(total_data, safe=False)



def get_orders_chart_api(request):
    rq_order = Order.objects.filter(product__policy_name='R, Q').count()
    ss_order = Order.objects.filter(product__policy_name='s, S').count()
    ts_order = Order.objects.filter(product__policy_name='T, S').count()
    data = {
       's, S': ss_order,
       'R, Q': rq_order,
       'T, S': ts_order 
    }
    return JsonResponse(data)



def get_product_chart_api(request):
    ts = PeriodicReviewTSPolicy.objects.all().count()
    ss = ContinuousReviewSSPolicy.objects.all().count()
    rq = ContinuousReviewRQPolicy.objects.all().count()
    data = {
       's, S Policy': ss,
       'R, Q Policy': rq,
       'T, S Policy': ts 
    }
    return JsonResponse(data)



def get_inventory_data_api(request):

    # Get the current date
    current_date = timezone.now()
    
    # Initialize lists
    month_list = []
    inventory_level_quantity_list = []
    order_qty = []
    all_products_orders = Order.objects.all()
    data = []
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

        for product in Product.objects.all():
            product_id = product.id
            # Aggregate inventory level quantities for the current month
            inventory_level_quantity = InvetorylevelUpdate.objects.filter(
                product_id=product_id,
                created_at__gte=first_day,
                created_at__lte=last_day
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
            
            # Assuming 'all_products_orders' is your queryset containing all orders for all products
            order_qty_in_month_total = all_products_orders.filter(
                product_id = product_id,
                created_at__gte=first_day,
                created_at__lte=last_day
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
            
            inventory_level_quantity_list.append(inventory_level_quantity)
            order_qty.append(order_qty_in_month_total)

            data.append({
                'Month': month_year,
                'Product': str(product),
                'InvetoryLevel': inventory_level_quantity,
                'OrderQuantity': order_qty_in_month_total,
            })

    
    return JsonResponse(data, safe=False)



def get_order_data_api(request):
    # Get the counts of orders for each status for the given product
    data = []
    for product in Product.objects.all():
        data.append({
            'Product': str(product),
            'Awaiting': Order.objects.filter(product=product, status = 'Awaiting').count(),
            'Completed': Order.objects.filter(product=product, status = 'Completed').count()
        })

    return JsonResponse(data, safe=False)



def get_stockout_data_api(request):
    # Get the current date
    current_date = timezone.now()
    
    data = []
    
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
        
        for product in Product.objects.all():
            # Count stockouts for the current month
            stockout_count = InvetorylevelUpdate.objects.filter(
                product=product,
                created_at__gte=first_day,
                created_at__lte=last_day,
                is_stockout=True
            ).count()
            
            data.append({
                'Product': str(product),
                'TotalStockCount': stockout_count,
                'Month': month_year
            })
        
    return JsonResponse(data, safe=False)





def get_estimated_days_data_api(request):

    all_orders = Order.objects.filter(status='Completed').order_by('id')

    data = []
    for order in all_orders:
        data.append({
            'id': order.id,
            'Product': str(order.product),
            'Order': str(order),
            'EstimatedDays': order.estimated_days,
            'LeadTime': order.get_lead_time()
        })

    return JsonResponse(data, safe=False)

