from django.urls import path
from . import views
from . import apis

app_name = 'products'

urlpatterns = [
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('products', views.all_products_view, name='all-products'),
    path('products/<str:policy_name>/add', views.add_product_view, name='add-product'),
    path('products/<policy_name>/<product_id>/edit', views.edit_product_view, name='edit-product'),
    path('products/<product_id>/delete', views.delete_product_view, name='delete-product'),
    path('search', views.search_products, name='search-products'),
    



    path('orders', views.all_orders_view, name='all-orders'),
    path('orders/create', views.create_order_view, name='create-order'),
    path('orders/<int:order_id>/edit', views.edit_order_view, name='edit-order'),
    path('orders/<int:order_id>/delete', views.delete_order_view, name='delete-order'),
    
    path('notifications', views.all_notifications_view, name='all-notifications'),
    
    path('api/get_products_api', apis.get_products_api, name='get_products'),
    path('api/get_inventory_levels_chart_api', apis.get_inventory_levels_chart_api, name='get_inventory_levels_chart_api'),
    path('api/get_orders_chart_api', apis.get_orders_chart_api, name='get_orders_chart_api'),
    path('api/get_product_chart_api', apis.get_product_chart_api, name='get_product_chart_api'),
    

    path('api/get_inventory_data_api', apis.get_inventory_data_api, name='get_inventory_data_api'),
    path('api/get_order_data_api', apis.get_order_data_api, name='get_order_data_api'),
    path('api/get_stockout_data_api', apis.get_stockout_data_api, name='get_stockout_data_api'),
    path('api/get_estimated_days_data_api', apis.get_estimated_days_data_api, name='get_estimated_days_data_api'),



    

]
