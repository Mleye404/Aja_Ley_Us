from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from orders.models import Order
from products.models import Product, ProductImage
from django.contrib.auth.models import User
from .forms import OrderUpdateForm, ProductForm, StaffAuthenticationForm


class AdminLoginView(LoginView):
    authentication_form = StaffAuthenticationForm
    template_name = "dashboard/login.html"
    next_page = "dashboard:home"


class AdminLogoutView(LogoutView):
    next_page = "dashboard:login"


@require_POST
def admin_logout(request):
    return AdminLogoutView.as_view()(request)


@staff_member_required(login_url="dashboard:login")
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


@staff_member_required(login_url="dashboard:login")
def order_list(request):
    orders = Order.objects.select_related("user").prefetch_related("items")
    query = request.GET.get("q", "").strip()
    search_term = query.lstrip("#")
    status = request.GET.get("status", "")
    if search_term:
        orders = orders.filter(
            Q(number__icontains=search_term) | Q(reference__icontains=search_term)
            | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)
            | Q(phone__icontains=search_term) | Q(email__icontains=search_term)
        )
    if status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    return render(request, "dashboard/order_list.html", {
        "orders": orders,
        "query": query,
        "selected_status": status,
        "status_choices": Order.STATUS_CHOICES,
    })


@staff_member_required(login_url="dashboard:login")
def order_update(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    if request.method == "POST":
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"La commande {order.display_number} a été mise à jour.")
            return redirect("dashboard:order_update", pk=order.pk)
    else:
        form = OrderUpdateForm(instance=order)
    return render(request, "dashboard/order_detail.html", {"order": order, "form": form})


@staff_member_required(login_url="dashboard:login")
def product_list(request):
    products = Product.objects.select_related("category").prefetch_related("images")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(name__icontains=query)
    return render(request, "dashboard/product_list.html", {"products": products, "query": query})


@staff_member_required(login_url="dashboard:login")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            photo = form.cleaned_data.get("photo")
            if photo:
                ProductImage.objects.create(product=product, image=photo)
            messages.success(request, f"Le produit « {product.name} » a été créé.")
            return redirect("dashboard:products")
    else:
        form = ProductForm()
    return render(request, "dashboard/product_form.html", {"form": form, "page_title": "Nouveau produit"})


@staff_member_required(login_url="dashboard:login")
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            photo = form.cleaned_data.get("photo")
            if photo:
                existing_photo = product.images.first()
                if existing_photo:
                    existing_photo.image = photo
                    existing_photo.save()
                else:
                    ProductImage.objects.create(product=product, image=photo)
            messages.success(request, f"Le produit « {product.name} » a été mis à jour.")
            return redirect("dashboard:products")
    else:
        form = ProductForm(instance=product)
    return render(request, "dashboard/product_form.html", {
        "form": form,
        "page_title": f"Modifier {product.name}",
        "product": product,
    })


@staff_member_required(login_url="dashboard:login")
@require_POST
def product_toggle_availability(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save(update_fields=["is_available", "updated_at"])
    if product.is_available:
        messages.success(request, f"« {product.name} » est de nouveau disponible.")
    else:
        messages.success(request, f"« {product.name} » est marqué indisponible et ne peut plus être commandé.")
    return redirect("dashboard:products")


@staff_member_required(login_url="dashboard:login")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product_name = product.name
        product.delete()
        messages.success(request, f"Le produit « {product_name} » a été supprimé.")
        return redirect("dashboard:products")
    return render(request, "dashboard/product_confirm_delete.html", {"product": product})
