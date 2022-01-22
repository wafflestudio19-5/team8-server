from django.db import models

from user.models import User
from location.models import Location
from article.models import Article

class Temparature(models.Model): 
    user = models.OneToOneField(User, related_name = "temparature", on_delete=models.CASCADE)
    temparature = models.FloatField(default=36.5)
    viewed_at = models.DateTimeField()

    
class Review(models.Model):
    
    REVIEW_TYPE_CHOICES = (
        ("buyer", "buyer"),
        ("seller", "seller"),
        ("user", "user"),
    )
    
    MANNER_TYPE_CHOICES = (
        ("good", "good"),
        ("bad", "bad"),
    )
    
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    reviewer = models.ForeignKey(User, related_name="review_by", on_delete=models.SET_NULL, null=True)
    reviewyee = models.ForeignKey(User, related_name="review_about", on_delete=models.CASCADE)

    article = models.ForeignKey(Article, null=True, default=None, on_delete=models.CASCADE)
    
    review = models.CharField(max_length=255)
    review_location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True) #null=False
    created_at = models.DateTimeField(auto_now_add=True)
    
    manner_type = models.CharField(max_length=20, choices = MANNER_TYPE_CHOICES)
    manner = models.CharField(max_length=100)