import os
import threading
import time
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Order, Payment
from schemas import payment_schema
from services.mpesa import MpesaService

payments_bp = Blueprint("payments", __name__, url_prefix="/api/v1/payments")

# We're not processing real M-Pesa transactions right now. The STK push
# still goes out to the phone correctly, but since there's no real money
# moving, Safaricom's sandbox callback is unreliable (often it just never
# arrives). Auto-completing the payment locally after a short delay lets
# the rest of the flow (order -> paid, animal -> sold) work end-to-end for
# testing/demo purposes. Set MPESA_AUTO_COMPLETE=false once real payments
# are wired up, so a genuine webhook is required instead.
MPESA_AUTO_COMPLETE = os.environ.get("MPESA_AUTO_COMPLETE", "true").lower() == "true"
MPESA_AUTO_COMPLETE_DELAY = int(os.environ.get("MPESA_AUTO_COMPLETE_DELAY", "10"))


class PaymentController:
    #.........................................

    @staticmethod
    def initiate_payment(order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return None, "Order not found"

        if order.status not in ("confirmed", "paid"):
            return None, "Order is not ready for payment"

        # Reuse an existing payment row instead of creating a second one for
        # the same order (Order.payment is one-to-one) — avoids orphaned
        # duplicate rows when a failed/pending payment is retried.
        payment = Payment.query.filter_by(order_id=order.id).first()
        if payment and payment.status == "completed":
            return None, "This order has already been paid for"

        if payment:
            payment.amount = order.total_amount
            payment.status = "pending"
        else:
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                method="mpesa",
                status="pending",
            )
            db.session.add(payment)
        db.session.commit()

        try:
            mpesa_response = MpesaService.stk_push(
                phone_number=order.recipient_phone,
                amount=order.total_amount,
                account_reference=f"order-{order.id}",
            )
        except Exception as e:
            payment.status = "failed"
            db.session.commit()
            return None, f"M-Pesa request failed: {str(e)}"

        payment.transaction_ref = mpesa_response.get("CheckoutRequestID")
        db.session.commit()

        if MPESA_AUTO_COMPLETE:
            # Fire-and-forget: simulate Safaricom's callback ourselves after
            # a short delay so we don't have to wait on/rely on the sandbox.
            app = current_app._get_current_object()
            threading.Thread(
                target=PaymentController._auto_complete_after_delay,
                args=(app, payment.id, MPESA_AUTO_COMPLETE_DELAY),
                daemon=True,
            ).start()

        return payment, None

    @staticmethod
    def _auto_complete_after_delay(app, payment_id, delay):
        """Runs on a background thread — needs its own app context since
        the request that triggered it will already have finished."""
        time.sleep(delay)
        with app.app_context():
            payment = db.session.get(Payment, payment_id)
            # Only complete it if it's still pending — if the real webhook
            # (or an admin/manual action) already resolved it, leave it alone.
            if not payment or payment.status != "pending":
                return
            PaymentController.handle_webhook(payment.transaction_ref, result_code=0)

    @staticmethod
    def handle_webhook(checkout_request_id, result_code):
        payment = Payment.query.filter_by(transaction_ref=checkout_request_id).first()
        if not payment:
            return

        if result_code == 0:
            payment.status = "completed"
            payment.order.status = "paid"
            for item in payment.order.items:
                item.animal.status = "sold"
        else:
            payment.status = "failed"
            for item in payment.order.items:
                item.animal.status = "available"

        db.session.commit()


@payments_bp.route("/initiate", methods=["POST"])
@jwt_required()
def initiate_payment():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    if not order_id:
        return jsonify(error="order_id is required"), 400

    user_id = get_jwt_identity()
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(error="Order not found"), 404
    if order.buyer_id != int(user_id):
        return jsonify(error="Not authorized to pay for this order"), 403

    payment, error = PaymentController.initiate_payment(order_id)
    if error:
        return jsonify(error=error), 400

    return jsonify(
        message="Payment initiated. Check your phone to complete the transaction.",
        payment=payment_schema.dump(payment),
    ), 201


@payments_bp.route("/webhook", methods=["POST"])
def mpesa_webhook():
    data = request.get_json(silent=True) or {}
    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_request_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")

    PaymentController.handle_webhook(checkout_request_id, result_code)

    return jsonify(ResultCode=0, ResultDesc="Accepted"), 200