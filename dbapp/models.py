from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
import subprocess

class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField()
    user_address = models.TextField()
    user_phoneNum = models.CharField(max_length=15)

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_user = models.ForeignKey('Users', on_delete=models.CASCADE)

def run_geocode_on_delete(sender, instance, **kwargs):
    """ 데이터 삭제 후 geocode.py 실행 """
    try:
        subprocess.run(["python", "webapp/geocode.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running geocode.py: {e}")

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("이메일이 필요합니다.")
        email = self.normalize_email(email)
        user = self.model(
            user_userid=username, user_email=email
        )  # user_userid와 user_email을 사용
        user.set_password(password)  # 비밀번호 해시화
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Users(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)  # 사용자 고유 ID
    user_userid = models.CharField(max_length=50, unique=True)  # 사용자 계정 아이디
    user_email = models.EmailField(max_length=100, unique=True)  # 이메일
    user_name = models.CharField(max_length=255)  # 이름
    user_address = models.CharField(max_length=255, blank=True)  # 주소
    user_phoneNum = models.CharField(max_length=11, blank=True)  # 휴대폰
    user_created_at = models.DateTimeField(auto_now_add=True)  # 계정 생성 날짜
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "user_userid"  # 로그인할 때 사용할 필드
    REQUIRED_FIELDS = ["user_email"]  # 추가로 요구할 필드

    def __str__(self):
        return self.user_userid


# models.py
from django.db import models


# 카테고리 모델
class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    category_description = models.TextField()

    def __str__(self):
        return self.category_name


# 상품 모델
class Product(models.Model):
    product_user = models.ForeignKey(Users, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True, null=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=0)
    product_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="categorized_products",
    )
    product_status = models.CharField(max_length=20, default="판매 중")
    product_created_at = models.DateTimeField(auto_now_add=True)
    product_updated_at = models.DateTimeField(auto_now=True)
    product_image_url = models.ImageField(
        upload_to="product_images/", blank=True, null=True
    )  # 변경된 부분
    product_wish_count = models.IntegerField(default=0)

    class Meta:
        db_table = "dbapp_product"

    def __str__(self):
        return self.product_name


class UserProduct(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class Review(models.Model):
    review_user = models.ForeignKey(Users, on_delete=models.CASCADE)
    review_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    review_rating = models.IntegerField()
    review_comment = models.TextField(blank=True, null=True)
    review_created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    message_sender = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="sent_messages"
    )
    message_receiver = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="received_messages"
    )
    message_content = models.TextField()
    message_sent_at = models.DateTimeField(auto_now_add=True)
    message_read_status = models.BooleanField(default=False)


class Wishlist(models.Model):
    wishlist_user = models.ForeignKey(Users, on_delete=models.CASCADE)
    wishlist_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    wishlist_added_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    notification_user = models.ForeignKey(Users, on_delete=models.CASCADE)
    notification_message = models.TextField()
    notification_type = models.CharField(max_length=50)
    notification_read_status = models.BooleanField(default=False)
    notification_created_at = models.DateTimeField(auto_now_add=True)


class MyShop(models.Model):
    user = models.OneToOneField(
        Users, on_delete=models.CASCADE, related_name="db_myshop"
    )  # related_name 추가
    shop_image = models.ImageField(
        upload_to="shop_images/",
        default="shop_images/default_image.png",
        blank=True,
        null=True,
    )
    # Users 테이블의 user_id를 외래 키로 참조
    shop_name = models.CharField(max_length=100, null=False)  # 상점 이름
    shop_info = models.TextField(blank=True, null=True)  # 상점 정보

    def __str__(self):
        return self.shop_name

#카운팅클래스
class SearchCount(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="search_count")
    count = models.IntegerField(default=0)
    last_reset = models.DateField(auto_now_add=True)

    def increment(self):
        """검색 횟수를 1씩 증가시키는 메서드"""
        self.count += 1
        self.save()

    def reset_daily(self):
        """자정에 검색 횟수를 초기화하는 메서드"""
        if self.last_reset < timezone.now().date():
            self.count = 0
            self.last_reset = timezone.now().date()
            self.save()

    def __str__(self):
        return f"{self.product.product_name} - 검색 횟수: {self.count}"

#검색 데이터 모델  
class SearchQuery(models.Model):
    keyword = models.CharField(max_length=100)
    user_id = models.CharField(max_length=50)  # 사용자 ID
    search_time = models.DateTimeField(default=timezone.now)

class VisitCount(models.Model):
    date = models.DateField(default=timezone.now)
    count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.date} 방문 수: {self.count}"