from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'food_ordering'

urlpatterns = [
    # Menu URLs
    path('', views.menu_view, name='menu'),
    path('category/<int:category_id>/', views.category_menu_view, name='category_menu'),
    path('category/<int:category_id>/items/', views.category_menu_view, name='category_menu'),
    path('search/', views.menu_search_view, name='menu_search'),
    
    # Order URLs
    path('order/start/', views.start_order, name='start_order'),
    path('order/item/<int:menu_item_id>/', views.add_item_to_order_form, name='add_item_to_order_form'),
    path('order/add/<int:menu_item_id>/', views.add_to_order, name='add_to_order'),
    path('order/view/', views.view_current_order, name='view_current_order'),  # Current order
    path('order/view/<int:order_id>/', views.view_order_detail, name='view_order_detail'),  # Specific order
    path('order/item/update/<int:item_id>/', views.update_order_item, name='update_order_item'),
    path('order/item/remove/<int:item_id>/', views.remove_order_item, name='remove_order_item'),
    path('order/submit/', views.submit_order, name='submit_order'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order/checkout/<int:order_id>/', views.checkout, name='checkout'),
    
    # Other URLs
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('account/', views.account_view, name='account'),
    path('order/create/', views.create_order_form, name='create_order_form'),
]