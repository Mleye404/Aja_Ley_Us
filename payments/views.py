from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from orders.models import Order
from .models import Payment


def choose_method(request, reference):
    order = get_object_or_404(Order, reference=reference)
    if hasattr(order, "payment") and order.payment.status == "PAID":
        return redirect("orders:confirmation", reference=order.reference)

    if request.method == "POST":
        method = request.POST.get("method")
        if method in ["WAVE", "ORANGE_MONEY"]:
            Payment.objects.update_or_create(
                order=order, defaults={"method": method, "amount": order.total, "status": "PENDING"}
            )
            return redirect("payments:simulate", reference=order.reference)
    return render(request, "payments/choose_method.html", {"order": order})


def simulate(request, reference):
    """Simulation réaliste du paiement (aucune vraie API Wave / Orange Money branchée)."""
    order = get_object_or_404(Order, reference=reference)
    payment = getattr(order, "payment", None)
    if not payment:
        return redirect("payments:choose", reference=order.reference)

    if request.method == "POST":
        outcome = request.POST.get("outcome", "success")
        if outcome == "success":
            payment.status = "PAID"
            order.status = "confirmed"
            messages.success(request, "Paiement confirmé avec succès.")
        else:
            payment.status = "FAILED"
            messages.error(request, "Le paiement a échoué. Vous pouvez réessayer.")
        payment.save()
        order.save()
        return redirect("orders:confirmation", reference=order.reference)

    return render(request, "payments/simulate.html", {"order": order, "payment": payment})
