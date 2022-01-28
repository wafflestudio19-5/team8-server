from user.models import User
from article.models import Article
from review.models import Review


def manner_score(reviews):
        score = 0
        for review in reviews:
            score += sum([int(i) for i in review.manner])
        return score

def update_temparature(user):
        temp = 36.5
        article_cnt = Article.objects.filter(seller=user).count()
        article_sold_cnt = Article.objects.filter(seller=user, sold_at__isnull=False).count()
        article_bought_cnt = Article.objects.filter(buyer=user).count()
            
        reviews = Review.objects.filter(review_type="seller", manner_type="good", reviewyee=user)
        seller_good_manner = manner_score(reviews)
            
        reviews = Review.objects.filter(review_type="seller", manner_type="bad", reviewyee=user)
        seller_bad_manner = manner_score(reviews)
            
        reviews = Review.objects.filter(review_type="buyer", manner_type="good", reviewyee=user)
        buyer_good_manner = manner_score(reviews)
            
        reviews = Review.objects.filter(review_type="buyer", manner_type="bad", reviewyee=user)
        buyer_bad_manner = manner_score(reviews)
            
        reviews = Review.objects.filter(review_type="user", manner_type="bad", reviewyee=user)
        user_good_manner = manner_score(reviews)
            
        reviews = Review.objects.filter(review_type="user", manner_type="bad", reviewyee=user)
        user_bad_manner = manner_score(reviews)
            
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
            temp = 0
        elif temp>99:
            temp = 99
        user.temparature = temp
        user.save()