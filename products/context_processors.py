from .models import Notification

def notifications(request):
    # Fetch all notifications
    notifications_count = Notification.objects.filter(is_new=True).count()
    # Return a dictionary containing the notifications
    return {'notifications_count': notifications_count}
