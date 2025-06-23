from rest_framework import serializers
from .models import Notification  # Make sure the model exists

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
