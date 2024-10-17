# models.py
from django.db import models
from django.contrib.auth import get_user_model  # Use get_user_model to avoid circular imports

User = get_user_model()  # Get the custom user model

class CustomUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.user.username} at {self.timestamp}"

class ChatHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)  # Use DateTimeField for timestamp

    def __str__(self):
        return f'{self.user.username} - {self.timestamp}'

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link chat to a user
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.timestamp}'
