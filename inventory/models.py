from django.db import models
from accounts.models import CustomUser


# Inventory item data lives in Excel

class InventoryRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    category = models.CharField(max_length=100)
    item_name = models.CharField(max_length=200)
    size = models.CharField(max_length=50)
    length = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    quantity = models.IntegerField(default=1)
    description = models.TextField(blank=True, default='')
    requested_by = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,null=True,blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} ({self.status}) by {self.requested_by}"

class IssuedItem(models.Model):
    item_name = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    length = models.CharField(max_length=50)
    quantity = models.IntegerField()
    issued_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='accepted')