import os
import sys
import json
import time
import requests
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Django 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Django 프로젝트 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'login.settings')
application = get_wsgi_application()

from django.apps import apps

def save_user_locations_to_json():
    # Django 모델 로드
    Users = apps.get_model('dbapp', 'Users')
    Product = apps.get_model('dbapp', 'Product')

    # Google Geocoding API 키 가져오기
    api_key = settings.GEOCODE_API_KEY

    # JSON 파일 경로 설정
    po_json_path = os.path.join(
        settings.BASE_DIR, "webapp", "static", "data", "po.json"
    )

    # 기존 위치 데이터 로드
    if os.path.exists(po_json_path):
        with open(po_json_path, "r", encoding="utf-8") as f:
            location_data = json.load(f)
    else:
        location_data = []

    # 기존 데이터의 주소 및 사용자 ID 목록 생성 (중복 확인 및 무결성 검사용)
    existing_entries = {(entry["user_id"], entry["product_id"]): entry for entry in location_data}

    # 새로운 위치 데이터를 추가할 리스트 초기화
    new_location_data = []

    for user in Users.objects.all():
        # 각 사용자의 모든 제품 조회 (필드를 'product_user'로 변경)
        user_products = Product.objects.filter(product_user=user)
        
        for product in user_products:
            # 이미 존재하는 사용자 ID와 제품 ID 조합은 스킵
            if (user.user_id, product.id) in existing_entries:
                print(f"Skipping: {user.user_id} for product {product.id} (already exists)")
                continue

            try:
                # 주소를 Google Geocoding API로 요청
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={user.user_address}&key={api_key}"
                response = requests.get(url)
                result = response.json()

                if result["status"] == "OK":
                    location = result["results"][0]["geometry"]["location"]
                    new_entry = {
                        "user_id": user.user_id,
                        "user_name": user.user_name,
                        "address": user.user_address,
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "product_id": product.id,
                        "product_name": product.product_name,
                        }
                    new_location_data.append(new_entry)
                    print(f"Processed: {user.user_address} for product {product.id}")
                else:
                    print(f"Geocoding failed for {user.user_address}: {result['status']}")

                time.sleep(1)  # 요청 간 딜레이 추가

            except Exception as e:
                print(f"Error for {user.user_address}: {e}")

    # 무결성 검사: 누락된 항목이 있으면 수정하도록 데이터 병합
    for entry in new_location_data:
        existing_entries[(entry["user_id"], entry["product_id"])] = entry

    # 업데이트된 데이터를 JSON 파일로 저장
    location_data = list(existing_entries.values())
    with open(po_json_path, "w", encoding="utf-8") as f:
        json.dump(location_data, f, ensure_ascii=False, indent=4)
    print(f"Location data saved to {po_json_path}")

if __name__ == "__main__":
    save_user_locations_to_json()
