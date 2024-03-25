from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
admin.site.register(ContinuousReviewRQPolicy)
admin.site.register(PeriodicReviewTSPolicy)
admin.site.register(ContinuousReviewSSPolicy)
admin.site.register(InvetorylevelUpdate)
admin.site.register(Order)
admin.site.register(Notification)