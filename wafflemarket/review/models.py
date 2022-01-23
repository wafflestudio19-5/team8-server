import datetime

from django.db import models
from django.utils import timezone

from user.models import User
from location.models import Location
from article.models import Article

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
    review_location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    
    review = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    manner_type = models.CharField(max_length=20, choices = MANNER_TYPE_CHOICES)
    manner = models.CharField(max_length=100)
    

class Temparature(models.Model): 
    user = models.OneToOneField(User, related_name="tempfield", on_delete=models.CASCADE)
    temparature = models.FloatField(default=36.5)
    viewed_at = models.DateTimeField(null=True)
    
    '''
    def update_is_valid(self):
        if self.viewed_at is not None:
            now = timezone.now().isocalendar()
            now_year = now[0]
            now_week = now[1]
            
            last_view = self.viewed_at.isocalendar()
            last_view_year = last_view[0]
            last_view_week = last_view[1]
            
            different_week = now_week!=last_view_week
            different_year = now_week==last_view_week and now_year!=last_view_year
            
            return different_week or different_year
        else:
            return True
    '''
    
    @classmethod
    def manner_score(cls, reviews):
        score = 0
        for review in reviews:
            score += sum([int(i) for i in review.manner])
        return score
    
    def update(self):
        if 1==1:
            user = self.user
            temp = 36.5
            article_cnt = Article.objects.filter(seller=user).count()
            article_sold_cnt = Article.objects.filter(seller=user, sold_at__isnull=False).count()
            article_bought_cnt = Article.objects.filter(buyer=user).count()
            
            reviews = Review.objects.filter(review_type="seller", manner_type="good", reviewyee=user)
            seller_good_manner = self.manner_score(reviews)
            
            reviews = Review.objects.filter(review_type="seller", manner_type="bad", reviewyee=user)
            seller_bad_manner = self.manner_score(reviews)
            
            reviews = Review.objects.filter(review_type="buyer", manner_type="good", reviewyee=user)
            buyer_good_manner = self.manner_score(reviews)
            
            reviews = Review.objects.filter(review_type="buyer", manner_type="bad", reviewyee=user)
            buyer_bad_manner = self.manner_score(reviews)
            
            reviews = Review.objects.filter(review_type="user", manner_type="bad", reviewyee=user)
            user_good_manner = self.manner_score(reviews)
            
            reviews = Review.objects.filter(review_type="user", manner_type="bad", reviewyee=user)
            user_bad_manner = self.manner_score(reviews)
            
            if(article_cnt>=7):
                temp += 30
                temp += user_good_manner * 2.4 * 0.5
                temp -= user_bad_manner * 4.8
            elif(article_cnt>=5):
                temp += 20
                temp += user_good_manner * 1.2 * 0.5
                temp -= user_bad_manner * 2.4
            elif(article_cnt>=3):
                temp += 10
                temp += user_good_manner * 0.6 * 0.5
                temp -= user_bad_manner * 1.2
            elif(article_cnt>=2):
                temp += 5
                temp += user_good_manner * 0.3 * 0.5
                temp -= user_bad_manner * 0.6
            elif(article_cnt>=1):
                temp += 2.5
                temp += user_good_manner * 0.15 * 0.5
                temp -= user_bad_manner * 0.3
                
            if(article_cnt>=7):
                temp += 30
                temp += seller_good_manner * 2.4
                temp -= seller_bad_manner * 4.8 * 2
            elif(article_sold_cnt>=5):
                temp += 20
                temp += seller_good_manner * 1.2
                temp -= seller_bad_manner * 2.4 * 2
            elif(article_sold_cnt>=3):
                temp += 10
                temp += seller_good_manner * 0.6
                temp -= seller_bad_manner * 1.2 * 2
            elif(article_sold_cnt>=2):
                temp += 5
                temp += seller_good_manner * 0.3
                temp -= seller_bad_manner * 0.6 * 2
            elif(article_sold_cnt>=1):
                temp += 2.5
                temp += seller_good_manner * 0.15
                temp -= seller_bad_manner * 0.3 * 2
                
            if(article_bought_cnt>=7):
                temp += 30
                temp += buyer_good_manner * 2.4
                temp -= buyer_bad_manner * 4.8 * 2
            elif(article_bought_cnt>=5):
                temp += 20
                temp += buyer_good_manner * 1.2
                temp -= buyer_bad_manner * 2.4 * 2
            elif(article_bought_cnt>=3):
                temp += 10
                temp += buyer_good_manner * 0.6
                temp -= buyer_bad_manner * 1.2 * 2
            elif(article_bought_cnt>=2):
                temp += 5
                temp += buyer_good_manner * 0.3
                temp -= buyer_bad_manner * 0.6 * 2
            elif(article_bought_cnt>=1):
                temp += 2.5
                temp += buyer_good_manner * 0.15
                temp -= buyer_bad_manner * 0.3 * 2
                
            if temp<0:
                self.temparature = 0
            elif temp>99:
                self.temparature = 99
            else:
                self.temparature = temp
            self.save()