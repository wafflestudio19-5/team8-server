from django.db import models
from user.models import User
from location.models import Location

class Article(models.Model):
    seller = models.ForeignKey(User, related_name='articles', on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, related_name='articles', on_delete=models.CASCADE, null=True)
    location = models.ForeignKey(Location, related_name='articles', null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=20)
    content = models.CharField(max_length=255)
    product_image = models.ImageField(blank=True, upload_to="photo/%Y/%m/%d") #image-upload 브랜치에서 수정 예정
    category = models.CharField(max_length=20)
    price = models.SmallIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, default=None)
    deleted_at = models.DateTimeField(null=True, default=None)
