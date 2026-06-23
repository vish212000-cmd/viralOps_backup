from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginInitiateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    mfa_token = serializers.CharField(required=False, allow_blank=True)

class LoginVerifyOTPSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()

class PasswordResetRequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    password = serializers.CharField(write_only=True)
