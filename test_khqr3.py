from bakong_khqr import KHQR

khqr = KHQR()
try:
    qr = khqr.create_qr(
        account_id="pNiGKZdBf8OMDhiIiRa5TmzCZiYJ16tB",
        merchant_name="TG TELE168 App",
        merchant_city="Phnom Penh",
        amount=29.0,
        currency="USD"
    )
    print("QR String:", qr)
except Exception as e:
    print("Error:", e)
