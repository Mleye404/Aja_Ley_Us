from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from orders.models import Order
from products.models import Product
from django.contrib.auth.models import User


@staff_member_required
def dashboard_home(request):
    orders = Order.objects.all()
    context = {
        "total_orders": orders.count(),
        "pending_orders": orders.filter(status=Order.STATUS_PENDING).count(),
        "preparing_orders": orders.filter(status=Order.STATUS_PREPARING).count(),
        "delivered_orders": orders.filter(status=Order.STATUS_DELIVERED).count(),
        "total_customers": User.objects.filter(is_staff=False).count(),
        "total_products": Product.objects.count(),
        "promo_products": Product.objects.on_promo().count(),
        "revenue": orders.filter(status__in=[Order.STATUS_CONFIRMED, Order.STATUS_PREPARING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]).aggregate(s=Sum("total"))["s"] or 0,
        "recent_orders": orders.select_related("user").prefetch_related("items").order_by("-created_at")[:8],
        "status_breakdown": orders.values("status").annotate(count=Count("id")),
    }
    return render(request, "dashboard/home.html", context)
