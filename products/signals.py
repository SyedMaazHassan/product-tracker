from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from .models import *
from django.utils import timezone

@receiver(post_save, sender=Order)
def update_related_policy(sender, instance, **kwargs):
    product_policy = instance.product.get_policy()
    product_policy_instance = product_policy['instance']
    product_policy_instance.calculate()


@receiver(pre_save, sender=Order)
def set_completed_at(sender, instance, **kwargs):
    # Check if the status is set to 'Completed'
    if instance.status == 'Completed':
        # Set completed_at to the current time
        instance.completed_at = timezone.now()

@receiver(post_save, sender=Product)
def update_inventory_level_update(sender, instance, **kwargs):
    is_already_exists = InvetorylevelUpdate.objects.filter(
        product = instance,
        quantity = instance.inventory_level, 
        is_stockout = instance.inventory_level < 1,
        created_at = timezone.now().date()
    ).exists()
    if not is_already_exists:
        InvetorylevelUpdate.objects.create(
            product = instance,
            quantity = instance.inventory_level, 
            is_stockout = instance.inventory_level < 1,            
        )


    # Check if stock level is low
    if instance.stock_level == 'Low':
        subject = 'Low Stock Alert'
        body = f'The stock level for {instance.product_name} is low. Consider restocking soon.'
        # Check if a notification already exists for this condition
        existing_notification = Notification.objects.filter(
            product=instance,
            subject=subject,
            body = body
        ).first()
        if existing_notification:
            existing_notification.body = body
            existing_notification.is_new = True
            existing_notification.save()
        else:
            Notification.objects.create(product=instance, subject=subject, body=body)

    # Check if inventory level is less than 1 (stockout)
    if instance.inventory_level < 1:
        subject = 'Stockout Alert'
        body = f'The product {instance.product_name} is out of stock. Please take immediate action to replenish inventory.'
        # Check if a notification already exists for this condition
        existing_notification = Notification.objects.filter(
            product=instance,
            subject=subject,
            body = body
        ).first()
        if existing_notification:
            existing_notification.body = body
            existing_notification.is_new = True
            existing_notification.save()
        else:
            Notification.objects.create(product=instance, subject=subject, body=body)



