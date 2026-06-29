from bakong_khqr import KHQR

def test_khqr():
    try:
        # Looking at documentation format
        khqr = KHQR()
        print("KHQR class instantiated successfully")
        print("Available methods:", [m for m in dir(khqr) if not m.startswith('_')])
    except Exception as e:
        print("Error:", e)

test_khqr()
