from rest_framework import serializers

class SummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    by_status = serializers.ListField()
    by_priority = serializers.ListField()

class SimpleSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    by_status = serializers.ListField()