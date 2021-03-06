from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit

from django.db import models

from user.models import User
from user.services import upload_product_image
from location.models import Location


class Article(models.Model):
    seller = models.ForeignKey(
        User, related_name="articles_sold", null=True, on_delete=models.SET_NULL
    )
    buyer = models.ForeignKey(
        User, related_name="articles_bought", null=True, on_delete=models.SET_NULL
    )
    location = models.ForeignKey(
        Location, related_name="articles", null=True, on_delete=models.SET_NULL
    )
    liked_users = models.ManyToManyField(
        User, blank=True, related_name="liked_articles"
    )
    title = models.CharField(max_length=20)
    content = models.CharField(max_length=255)
    category = models.CharField(max_length=20)
    price = models.PositiveBigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, default=None)
    hit = models.PositiveBigIntegerField(default=0)
    like = models.PositiveBigIntegerField(default=0)

    def update(
        self, title=None, content=None, product_image=None, category=None, price=None, **kwargs,
    ):
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if product_image is not None:
            self.product_image = product_image
        if category is not None:
            self.category = category
        if price is not None:
            self.price = price


class Comment(models.Model):
    commenter = models.ForeignKey(
        User, related_name="comments", null=True, on_delete=models.SET_NULL
    )
    article = models.ForeignKey(
        Article, related_name="comments", on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        "self", related_name="replies", null=True, on_delete=models.SET_NULL
    )
    content = models.CharField(max_length=120, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, default=None)


class ProductImage(models.Model):
    article = models.ForeignKey(
        Article, related_name="product_images", null=False, on_delete=models.CASCADE
    )
    product_image = models.ImageField(upload_to=upload_product_image)
    product_thumbnail = ProcessedImageField(
        null=True,
        upload_to=upload_product_image,
        processors=[ResizeToFit(height=120)],
        format="JPEG",
    )
