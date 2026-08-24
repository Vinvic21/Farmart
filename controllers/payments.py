from flask import Blueprint, request, jsonify
from extensions import db
from models import Order, Payment
from services.mpesa import MpesaService

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


class PaymentController:
    @staticmethod
    def initiate_payment(order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, "Order not found"

        if order.status != "confirmed":
            return None, "Order is not ready for payment"

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

        return payment, None

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
def initiate_payment():
    data = request.get_json()
    order_id = data.get("order_id")
    if not order_id:
        return jsonify(error="order_id is required"), 400

    payment, error = PaymentController.initiate_payment(order_id)
    if error:
        return jsonify(error=error), 400

    return jsonify(
        message="Payment initiated. Check your phone to complete the transaction.",
        payment_id=payment.id,
        status=payment.status,
    ), 201


@payments_bp.route("/webhook", methods=["POST"])
def mpesa_webhook():
    data = request.get_json()
    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_request_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")

    PaymentController.handle_webhook(checkout_request_id, result_code)

    return jsonify(ResultCode=0, ResultDesc="Accepted"), 200