from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = (
    [
        path("", views.main, name="main"),
        path('admin_page/', views.admin_page, name='admin_page'),  # URL 패턴 설정
        path('api/admin/products/', views.admin_product_list, name='admin_product_list'),  # 관리자 전용 상품 목록 API
        path('api/admin/products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
        path('api/admin/users/', views.admin_user_list, name='admin_user_list'),
        path('api/admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
        path('api/admin/recent-products/', views.recent_uploaded_products, name='recent_uploaded_products'),
        path('api/admin/category-product-count/', views.category_product_count, name='category_product_count'),
        path('api/admin/today-uploaded-count/', views.today_uploaded_count, name='today-uploaded-count'),
        path('api/admin/today-visited-count/', views.today_visited_count, name='today_visited_count'),
        path('api/admin/today-signup-count/', views.today_signup_count, name='today_signup_count'),  # API 경로 추가
        path('api/admin/weekly-signup-trend/', views.weekly_signup_trend, name='weekly_signup_trend'),
        path("sign-in/", views.sign_in, name="sign_in"),
        path("sign-up/", views.sign_up, name="sign_up"),
        path("login/", views.sign_in, name="login"),
        path("map_page/", views.map_page, name="map_page"),
        path("logout/", auth_views.LogoutView.as_view(), name="logout"),
        path("my_page/", views.my_page, name="my_page"),
        path("product_sale/", views.product_sale, name="product_sale"),
        path("product/edit/<int:product_id>/", views.product_edit, name="product_edit"),  # 추가된 URL
        path("update_my_shop/", views.update_my_shop, name="update_my_shop"),
        path("product/<int:pk>/", views.product_detail, name="product_info"),
        path("product/<int:pk>/", views.product_info, name="product_info"),
        path("products/", views.product_list, name="product_list"),
        path("category/<int:category_id>/", views.category_view, name="category_view"),
        path("category/<int:id>/", views.category_detail, name="category_detail"),
        path("product/edit/<int:product_id>/",views.edit_product_view,name="edit_product"),  # 수정 URL 추가
        path("edit_product/", views.edit_product, name="edit_product"),  # URL 패턴 추가
        path("search/", views.search, name="search"),
        path("autocomplete/", views.autocomplete, name="autocomplete"),
        path("predict-category/", views.predict_category, name="predict_category"),
        path('execute-geocode/', views.execute_geocode, name='execute_geocode'),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
