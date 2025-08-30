from django.urls import path, include
from . import views
from . import api_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    # path('generate_blog/', views.generate_blog, name='generate_blog'),
    path('blog_list/', views.blog_list, name='blog_list'),
    path('blog_details/<int:pk>/', views.blog_details, name='blog_details'),
    # path('generate-blog-fast/', views.generate_blog_fast, name='generate_blog_fast'),
    path('generate_blog_smart/', views.generate_blog_smart, name='generate_blog_smart'),
    path('api/generate-blog/', api_views.generate_blog_api, name='generate_blog_api'),
    path('api/blogs/', api_views.blog_list_api, name='blog_list_api'),
    path('api/blogs/<int:pk>/', api_views.blog_detail_api, name='blog_detail_api'),
    path('api/blogs/<int:pk>/delete/', api_views.blog_delete_api, name='blog_delete_api'),
]