from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from dbapp.models import Users, Category, MyShop, Product, SearchQuery,VisitCount
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.http import JsonResponse  # JSON 반응형
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.views import View
from django.core.paginator import Paginator
from dbapp.forms import ProductForm
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.db.models import Count, F
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
import numpy as np
from django.http import JsonResponse
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.xception import preprocess_input
from io import BytesIO  # 추가: 파일 변환을 위해 BytesIO를 임포트
from .geocode import save_user_locations_to_json
import subprocess

import re
import os

model = load_model('webapp/models/xception_fine_tuned.h5')



def increment_visit_count():
    today = timezone.now().date()
    visit_count, created = VisitCount.objects.get_or_create(date=today)
    visit_count.count += 1
    visit_count.save()

def main(request):
    increment_visit_count()  # 메인 페이지가 로드될 때 방문 수 증가
    products = Product.objects.all().order_by(
        "-product_created_at"
    )  # 최신 상품 순으로 정렬
    paginator = Paginator(products, 20)  # 한 페이지에 20개 상품
    page_number = request.GET.get("page")  # URL 쿼리 파라미터에서 페이지 번호 가져오기
    page_obj = paginator.get_page(page_number)  # 페이지 객체 생성
    return render(request, "webapp/main.html", {"page_obj": page_obj})

def edit_product(request):
    return render(request, "product/edit_product.html")  # HTML 템플릿 경로

def admin_page(request):
    return render(request, 'webapp/admin_page.html')

def admin_product_list(request):
    # 최신순으로 정렬하여 상품 목록을 가져옵니다.
    products = Product.objects.all().order_by('-product_created_at')  # 생성일 기준 내림차순 정렬
    product_data = [
        {
            "id": product.id,
            "product_name": product.product_name,
            "product_description": product.product_description,
            "product_price": product.product_price,
            "product_status": product.product_status,
            "product_created_at": product.product_created_at,
        }
        for product in products
    ]
    return JsonResponse(product_data, safe=False)

def today_visited_count(request):
    today = timezone.now().date()
    # 오늘 방문 횟수 가져오기 또는 새로 생성
    visit_count, created = VisitCount.objects.get_or_create(date=today)
    
    # 반환할 데이터
    return JsonResponse({'today_visited_count': visit_count.count})

@login_required  # 관리자만 접근 가능
def admin_user_list(request):
    if request.method == "GET":
        users = Users.objects.all().order_by('-user_created_at')
        user_data = []
        for user in users:
            user_data.append({
                'user_id': user.user_id,  # user.id 대신 user.user_id 사용
                'user_userid': user.user_userid,
                'user_email': user.user_email,
                'user_name': user.user_name,
                'user_address': user.user_address,
                'user_phoneNum': user.user_phoneNum,
                'user_created_at': user.user_created_at,
                'is_staff': user.is_staff,
            })
        return JsonResponse(user_data, safe=False)
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    try:
        user = Users.objects.get(user_id=user_id)  # 사용자 ID로 사용자 객체 가져오기
        user.delete()  # 사용자 삭제
        return JsonResponse({'message': '사용자 삭제 성공'}, status=204)
    except Users.DoesNotExist:
        return JsonResponse({'error': '사용자를 찾을 수 없습니다.'}, status=404)

@csrf_exempt  # CSRF 보호를 비활성화 (토큰이 제대로 작동하지 않는 경우에만 사용)
def delete_product(request, product_id):
    if request.method == 'DELETE':
        try:
            product = Product.objects.get(id=product_id)
            product.delete()
            return JsonResponse({'success': True})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': '상품을 찾을 수 없습니다.'}, status=404)
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)

def recent_uploaded_products(request):
    recent_products = Product.objects.order_by('-product_created_at')[:3]
    response_data = [{
        'id': product.id,
        'product_name': product.product_name,
        'product_price': product.product_price,
        'product_description': product.product_description,
        'product_created_at': product.product_created_at.isoformat(),
    } for product in recent_products]
    return JsonResponse(response_data, safe=False)

def category_product_count(request):
    categories = Category.objects.all()
    response_data = [{
        'category_name': category.category_name,
        'product_count': category.categorized_products.count()  # 관련된 상품 수
    } for category in categories]
    return JsonResponse(response_data, safe=False)

@api_view(['GET'])
def today_uploaded_count(request):
    # 오늘 날짜 기준으로 상품 수 집계
    today = timezone.now().date()
    count = Product.objects.filter(product_created_at__date=today).count()
    
    return Response({'count': count})

@api_view(['GET'])
def today_signup_count(request):
    # 오늘 날짜 기준으로 가입자 수 집계
    today = timezone.now().date()
    count = Users.objects.filter(user_created_at__date=today).count()  # 가입일자가 오늘인 사용자 수
    
    return Response({'today_signup_count': count})

@api_view(['GET'])
def weekly_signup_trend(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=7)

    # 지난 7일간의 가입자 수를 세기 위해 날짜별로 카운트
    signup_counts = (
        Users.objects.filter(user_created_at__range=(start_date, today))
        .extra(select={'signup_date': 'date(user_created_at)'})  # 날짜만 추출
        .values('signup_date')
        .annotate(count=Count('user_id'))  # 가입자 수 집계
        .order_by('signup_date')  # 날짜 기준으로 정렬
    )

    # 결과를 날짜별로 정리
    result = {str(date['signup_date']): date['count'] for date in signup_counts}

    # 지난 7일간의 모든 날짜에 대해 기본값을 0으로 초기화
    for i in range(7):
        date = (today - timedelta(days=i)).isoformat()  # 날짜 포맷
        result.setdefault(date, 0)  # 기본값 0 추가

    # 날짜를 최신 순서로 정렬
    sorted_result = [result[(today - timedelta(days=i)).isoformat()] for i in range(7)]

    return Response({'weekly_signup_counts': sorted_result})


def category_view(request, category_id):
    # 카테고리 ID로 카테고리 객체를 가져옵니다.
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(
        product_category=category
    ).order_by('-product_created_at')  # 해당 카테고리에 속하는 상품들을 필터링합니다.

    context = {
        "category_name": category.category_name,  # 카테고리 이름을 템플릿에 전달합니다.
        "products": products,
    }

    return render(request, "webapp/categori_page.html", context)


def map_page(request):
    return render(request, "webapp/map_page.html")


def product_list(request):
    image_folder = os.path.join(settings.STATIC_ROOT, "images/imageprod")
    image_files = []
    products = Product.objects.all()  # 모든 상품을 가져옵니다.
    return render(request, "webapp/product_list.html", {"products": products})
    # 이미지 폴더 내 모든 파일을 불러와 리스트에 저장
    if os.path.isdir(image_folder):
        for filename in os.listdir(image_folder):
            if filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_files.append(f"images/imageprod/{filename}")

    # 템플릿으로 이미지 파일 목록을 전달
    return render(request, "search.html", {"image_files": image_files})


def product_info(request, product_id):
    # 상품 정보를 가져옴
    product = get_object_or_404(Product, pk=product_id)

    # 상품 소유자(사용자)의 상점 이름 가져오기
    try:
        shop_name = product.product_user.db_myshop.shop_name
    except MyShop.DoesNotExist:
        shop_name = "상점 정보 없음"  # 상점이 없는 경우 처리
    except AttributeError:
        shop_name = "상점 정보 없음"  # db_myshop이 없을 때 처리

    context = {
        "product": product,
        "shop_name": shop_name,
    }
    return render(request, "webapp/product_info.html", context)


def category_detail(request, id):
    category = get_object_or_404(Category, id=id)
    return render(request, "category_detail.html", {"category": category})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "webapp/product_info.html", {"product": product})


@csrf_exempt
def update_my_shop(request):
    if request.method == "POST":
        shop_name = request.POST.get("shop_name")
        shop_info = request.POST.get("shop_info")
        shop_image = request.FILES.get("shop_image")

        # 현재 사용자의 MyShop 객체를 가져오는 코드
        my_shop, created = MyShop.objects.get_or_create(
            user=request.user
        )  # 사용자 ID를 기반으로 가져옴

        if shop_image:
            fs = FileSystemStorage()
            filename = fs.save(shop_image.name, shop_image)
            my_shop.shop_image = filename

        my_shop.shop_name = shop_name
        my_shop.shop_info = shop_info
        my_shop.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})


@login_required
def my_page(request):
    # 로그인한 사용자 정보를 가져옴
    user = request.user

    # MyShop 데이터 가져오기 (외래 키로 사용자와 연결된 데이터)
    try:
        myshop = MyShop.objects.get(user=user)
    except MyShop.DoesNotExist:
        myshop = None  # MyShop 데이터가 없을 경우

    # Product 데이터 가져오기 (product_user 필드로 사용자와 연결된 제품들)
    products = Product.objects.filter(product_user=request.user).order_by(
        "-product_created_at"
    )

    # 페이지당 표시할 개수 (기본값: 10)
    items_per_page = request.GET.get("items_per_page", 10)

    # 페이지네이터 설정
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 템플릿에 MyShop과 페이지네이션 객체, 현재 선택된 개수를 함께 전달
    return render(
        request,
        "webapp/my_page.html",
        {"myshop": myshop, "page_obj": page_obj, "items_per_page": int(items_per_page)},
    )


class ProductInfoView(DetailView):
    model = Product
    template_name = "product_info.html"
    context_object_name = "product"


def product_sale(request):
    if request.method == "POST":
        try:
            name = request.POST["name"]
            price = float(
                request.POST["price"].replace(",", "").strip()
            )  # 가격 포맷 정리
            description = request.POST["description"]
            category_id = request.POST["category"]
            image = request.FILES.get("image")  # .get()으로 안전하게 가져오기

            # 이미지 파일 저장 및 URL 생성
            image_url = None
            if image:
                image_name = image.name
                image_path = os.path.join(settings.MEDIA_ROOT, "imageprod", image_name)
                with open(image_path, "wb+") as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                image_url = os.path.join(settings.MEDIA_URL, "imageprod", image_name)

            # Product 모델에 저장
            product = Product(
                product_user=request.user,
                product_name=name,
                product_description=description,
                product_price=price,
                product_category_id=category_id,
                product_image_url=image_url,
            )
            product.save()

            messages.success(request, "상품이 등록되었습니다.")
            return redirect("my_page")

        except KeyError as e:
            messages.error(request, f"필드 '{e}'가 누락되었습니다.")
            return redirect("product_sale")
        except ValueError:
            messages.error(request, "가격을 올바르게 입력해주세요.")
            return redirect("product_sale")
        except Exception as e:
            messages.error(request, f"오류가 발생했습니다: {str(e)}")
            return redirect("product_sale")

    return render(request, "webapp/product_sale.html")


def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.product_name = request.POST["name"]
        product.product_description = request.POST["description"]
        product.product_price = request.POST["price"]

        # 이미지 파일 처리
        if "image" in request.FILES:
            product.product_image_url = handle_image_upload(request.FILES["image"])

        product.save()  # 변경된 내용을 데이터베이스에 저장

        return redirect("my_page")  # 수정 후 리다이렉트

    return render(request, "webapp/edit_product.html", {"product": product})

def predict_category(request):
    if request.method == "POST" and request.FILES.get('image'):
        # 이미지 파일을 BytesIO로 변환
        img = request.FILES['image']
        img = image.load_img(BytesIO(img.read()), target_size=(299, 299))  # 수정: BytesIO로 변환하여 읽음
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        predictions = model.predict(img_array)[0]
        categories = ["카테고리1", "카테고리2", "카테고리3", "카테고리4"]
        probabilities = {category: float(pred) for category, pred in zip(categories, predictions)}

        # 가장 높은 확률의 카테고리 선택
        best_category = categories[np.argmax(predictions)]

        response_data = {
            "probabilities": probabilities,
            "best_category": best_category
        }
        return JsonResponse(response_data)
    return JsonResponse({"error": "Invalid request"}, status=400)

def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()  # 변경사항 저장
            return redirect(
                "product_info", product_id=product.id
            )  # 수정 후 상품 상세 페이지로 리다이렉트
    else:
        form = ProductForm(instance=product)  # GET 요청 시 현재 상품 정보로 폼 초기화

    return render(
        request, "webapp/edit_product.html", {"product": product, "form": form}
    )


def sign_in(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        # 사용자 정보 조회
        try:
            user = Users.objects.get(user_userid=username)  # 사용자 ID로 검색
            # 비밀번호 확인
            if check_password(password, user.password):
                login(request, user)  # 로그인 처리
                messages.success(request, "로그인 성공!")
                return redirect("main")  # 성공적으로 로그인한 후 리디렉션할 URL
            else:
                messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
                return redirect("sign_in")  # 로그인 페이지로 리디렉션
        except Users.DoesNotExist:
            messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
            return redirect("sign_in")  # 로그인 페이지로 리디렉션

    return render(request, "webapp/sign_in.html")


def sign_up(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        password_confirm = request.POST["password_confirm"]
        name = request.POST["name"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        address = request.POST["address"]
        detail_address = request.POST["detail_address"]
        extra_address = request.POST["extra_address"]
        postcode = request.POST["postcode"]

        # 비밀번호 확인
        if password != password_confirm:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return redirect("sign_up")

        # 주소 합치기
        full_address = f"{address}, {detail_address}, {extra_address}".strip(", ")

        # 사용자 생성
        try:
            user = Users(
                user_userid=username,
                user_email=email,
                user_name=name,
                user_address=full_address,
                user_phoneNum=phone,
            )
            user.set_password(password)  # 비밀번호 해시화
            user.full_clean()  # 모델 검증
            user.save()  # 사용자 저장

            # 새로운 MyShop 객체 생성
            MyShop.objects.create(user=user)  # 사용자의 MyShop 객체 생성

            messages.success(request, "회원가입이 완료되었습니다.")
            return redirect("sign_in")
        except ValidationError as e:
            messages.error(
                request, f"입력값에 오류가 있습니다: {', '.join(e.messages)}"
            )
            return redirect("sign_up")
        except Exception as e:
            messages.error(request, f"오류가 발생했습니다: {str(e)}")
            return redirect("sign_up")

    return render(request, "webapp/sign_up.html")


# 검색 데이터 전처리
def preprocess_search_query(query):
    hangle = re.compile("[가-힣]+").findall(query)
    english = re.compile("[a-zA-Z]+").findall(query)
    number = re.compile("[0-9]+").findall(query)

    # 나뉜 각 부분을 합쳐서 리스트 형태로 반환
    return hangle + english + number


# 부적절한 검색어 목록
INVALID_KEYWORDS = ["개인정보", "성인", "불법", "마약", "무기", "특수기호"]


def is_valid_search_query(query):
    return not any(invalid_word in query for invalid_word in INVALID_KEYWORDS)


def preprocess_search_query(query):
    """
    검색어를 한글, 영문, 숫자로 나누어 전처리하는 함수.
    """
    hangle = re.compile("[가-힣]+").findall(query)
    english = re.compile("[a-zA-Z]+").findall(query)
    number = re.compile("[0-9]+").findall(query)

    # 나뉜 각 부분을 합쳐서 리스트 형태로 반환
    return hangle + english + number


# 검색 기능
def search(request):
    q = request.GET.get("q", "").strip()  # URL 쿼리 파라미터에서 검색어 가져오기

    # 검색어가 없는 경우 메인 페이지로 이동
    if not q:
        return render(request, "webapp/main.html", {"searched": "", "results": None})

    # 부적절한 검색어 검사
    if not is_valid_search_query(q):
        return render(
            request,
            "webapp/main.html",
            {
                "searched": q,
                "results": None,
                "error_message": "부적절한 검색어입니다. 다른 검색어를 입력해주세요.",
            },
        )

    # 검색어 전처리
    keywords = preprocess_search_query(q)

    # 전처리된 키워드를 사용해 DB에서 물품 필터링
    results = Product.objects.all()
    for keyword in keywords:
        results = results.filter(product_name__icontains=keyword)

    # 결과를 템플릿으로 전달
    return render(request, "webapp/search.html", {"searched": q, "results": results})


# 검색시 자동완성 결과 출력 기능
@require_GET
def autocomplete(request):
    query = request.GET.get("q", "").strip()  # 입력된 검색어 가져오기

    # 부적절한 검색어일 경우 빈 결과 반환
    if not is_valid_search_query(query):
        return JsonResponse({"results": []})

    # 검색어 전처리
    keywords = preprocess_search_query(query)

    # 전처리된 키워드를 사용해 DB에서 물품 필터링 (최대 5개 결과만 반환)
    products = Product.objects.all()
    for keyword in keywords:
        products = products.filter(product_name__icontains=keyword)
    products = products[:5]

    results = [
        {"id": product.id, "product_name": product.product_name} for product in products
    ]
    return JsonResponse({"results": results})


# 검색어 기록 함수
def record_search_keyword(user_id, keyword, is_popular_click=False):
    # 부적절한 검색어 필터링
    if not is_valid_search_query(keyword):
        return

    # 인기 검색어 클릭으로 검색된 경우 제외
    if is_popular_click:
        return

    # 동일 사용자 중복 검색어 체크 (24시간 내 동일 검색어 중복 방지)
    one_day_ago = timezone.now() - timedelta(days=1)
    if SearchQuery.objects.filter(
        user_id=user_id, keyword=keyword, search_time__gte=one_day_ago
    ).exists():
        return

    # 새로운 검색어 기록
    SearchQuery.objects.create(user_id=user_id, keyword=keyword)


# 인기 검색어 가져오기 함수
def get_popular_keywords():
    # 최근 1시간 동안 집계
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_keywords = SearchQuery.objects.filter(search_time__gte=one_hour_ago)

    # 인기 검색어 중 상위 10개만 반환
    popular_keywords = (
        recent_keywords.values("keyword")
        .annotate(count=Count("keyword"))
        .order_by("-count")
    )
    return [keyword["keyword"] for keyword in popular_keywords[:10]]

@csrf_exempt
def execute_geocode(request):
    if request.method == 'POST':
        try:
            # geocode.py 실행
            result = subprocess.run(
                ['python', 'webapp/geocode.py'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': result.stderr})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})