from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, UserManager
import requests
from random import randint
from django.utils import timezone
import time
import hashlib
import hmac
import base64
import datetime 
from location.models import Location

class CustomUserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(**extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
class Auth(models.Model):
    phone_number = models.CharField(max_length=255, unique=True)
    auth_number = models.CharField(max_length=255, null=True)
    sended_at = models.DateTimeField(auto_now=True)
    
    def create_auth_number(self):
        self.auth_number = randint(1000, 10000)
        self.save()
        #self.send_sms() # 인증번호가 담긴 SMS를 전송
        
    def send_sms(self):
        
        def make_signature(access_key, secret_key, method, uri, timestamp):
            secret_key = bytes(secret_key, 'UTF-8')
            message = method + " " + uri + "\n" + timestamp + "\n" + access_key
            message = bytes(message, 'UTF-8')
            signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
            return signingKey
    
        url = 'https://sens.apigw.ntruss.com/sms/v2/services/ncp:sms:kr:260182270275:wafflemarket/messages'
        timestamp = str(int(time.time() * 1000))
        uri = '/sms/v2/services/ncp:sms:kr:260182270275:wafflemarket/messages'
        access_key = "Ih1hTs3EV9rU2KxKUdiG"
        secret_key =  "R7CAqhYuxYbfOFTg8RFxhGcoq9SlczRiOAEOivR4"
        
        data = {
        "type":"SMS",
        "contentType" : "COMM",
        "countryCode" : "82",
        "from":"01086878061",
        "content": "[와플마켓] 인증 번호 [{}] *타인에게 절대 노출하지 마세요.(계정 도용 위험)".format(self.auth_number),
        "messages":[{"to": self.phone_number, 
                     "subject" : "string", 
                     "content" : "[와플마켓] 인증 번호 [{}] *타인에게 절대 노출하지 마세요.(계정 도용 위험)".format(self.auth_number)}]
        }
        headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp" : timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": make_signature(access_key, secret_key, 'POST', uri, timestamp)
        }
        requests.post(url, json=data, headers=headers)
        
    def authenticate(self, auth_number):
        time_limit = timezone.now() - datetime.timedelta(minutes=5)
        if auth_number==self.auth_number and self.sended_at>time_limit:
            return True
        else:
            return False

class User(AbstractBaseUser, PermissionsMixin):
    objects = CustomUserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    phone_number = models.CharField(max_length=255, null=True, unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, unique=True)
    # profile_image = models.ImageField(blank=True, upload_to="photo/%Y/%m/%d")
    location = models.ForeignKey(Location, related_name='users', null=True, on_delete=models.SET_NULL)
    
    interest = models.CharField(max_length=255, default = "1"*17)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    leaved_at = models.DateTimeField(null=True)
    last_login = models.DateTimeField(null=True)
    username_changed_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(null=True, default=False)
    
    def __str__(self):
        return self.username

