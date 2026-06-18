import inspect
from bakong_khqr import KHQR

print(inspect.signature(KHQR.__init__))
print(inspect.signature(KHQR.create_qr))
