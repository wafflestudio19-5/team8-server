from django.db import models
from user.models import User
from location.models import Location
from user.services import upload_product_image

class Article(models.Model):
    seller = models.ForeignKey(User, related_name='articles_sold', null=True, on_delete=models.SET_NULL)
    buyer = models.ForeignKey(User, related_name='articles_bought', null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, related_name='articles', null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=20)
    content = models.CharField(max_length=255)
    product_image = models.ImageField(blank=True, upload_to=upload_product_image)
    category = models.CharField(max_length=20)
    price = models.PositiveBigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, default=None)
    #deleted_at = models.DateTimeField(null=True, default=None)
    
    def update(self, title=None, content=None, product_image=None, category=None, price=None):
        if title is not None: self.title = title
        if content is not None: self.content = content
        if product_image is not None: self.product_image = product_image
        if category is not None: self.category = category
        if price is not None: self.price = price

class Comment(models.Model):
    commenter = models.ForeignKey(User, related_name='comments', null=True, on_delete=models.SET_NULL)
    article = models.ForeignKey(Article, related_name='articles', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    content = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, default=None)