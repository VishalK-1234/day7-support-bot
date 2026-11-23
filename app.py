"""Customer Support Bot (Day 7 Challenge: risk review).

A small Flask app. A customer sends a message, the LLM decides on a reply
and an action, and the app carries out the action.
"""
import time
import uuid
import json
import logging

from flask import Flask, jsonify, request

from llm import call_llm

app = Flask(__name__)

API_KEY = "sk-demo-4f9a2c71-FAKE-KEY-for-training-only"

logging.basicConfig(filename="logs/app.log", level=logging.INFO)

ORDERS = {
    "10231": {"status": "Shipped", "amount": 1299},
    "10232": {"status": "Delivered", "amount": 499},
    "10233": {"status": "Processing", "amount": 2499},
}
CUSTOMERS = {
    "ravi.kumar@example.com": {"name": "Ravi Kumar", "phone": "+91 98480 12345", "active": True},
    "priya.s@example.com": {"name": "Priya Sharma", "phone": "+91 99890 67890", "active": True},
}

CUSTOMER_TOKENS = {
    "ravi.kumar@example.com": "demo-token-ravi",
    "priya.s@example.com": "demo-token-priya",
}

REFUNDS = []


# ---------- Tools the LLM can use ----------

def get_order_status(order_id):
    order = ORDERS.get(order_id)
    return order["status"] if order else "Order not found"


def issue_refund(order_id, amount):
    order = ORDERS.get(order_id)

    if not order:
        return "Order not found"

    if amount <= 0:
        return "Invalid refund amount"

    if amount > order["amount"]:
        return "Refund amount exceeds order amount"

    REFUNDS.append({"order_id": order_id, "amount": amount})
    return f"Refunded Rs {amount} for order {order_id}"


def delete_customer_account(customer_email):
    CUSTOMERS.pop(customer_email, None)
    return f"Deleted account {customer_email}"


TOOLS = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "delete_customer_account": delete_customer_account,
}


# ---------- Chat endpoint ----------

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    email = data.get("customer_email", "")
    message = data.get("message", "")
    customer = CUSTOMERS.get(email)
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not customer or CUSTOMER_TOKENS.get(email) != token:
        return jsonify({"error": "Unauthorized"}), 401

    prompt = (
        "You are a helpful support agent. Reply in JSON with reply, action and args.\n"
        f"Customer name: {customer.get('name')}\n"
        f"Customer email: {email}\n"
        f"Customer phone: {customer.get('phone')}\n"
        f"Customer message: {message}"
    )

    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    text, usage = call_llm(prompt, API_KEY)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    estimated_cost = (input_tokens + output_tokens) * 0.0005

    logging.info(
        "AI_CALL request_id=%s model=%s latency_ms=%s "
        "input_tokens=%s output_tokens=%s cost_inr=%.4f",
        request_id,
        "dummy-llm",
        latency_ms,
        input_tokens,
        output_tokens,
        estimated_cost
    )
    result = json.loads(text)

    action = result.get("action")
    action_result = None
    if action:
        args = result.get("args", {})
        if args.get("customer_email") == "from_request":
            args["customer_email"] = email
        action_result = TOOLS[action](**args)

    logging.info("AI_REPLY request_id=%s completed=true", request_id)
    return jsonify({"reply": result["reply"], "action_result": action_result})


if __name__ == "__main__":
    app.run(debug=True)
