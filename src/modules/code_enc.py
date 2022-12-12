import cv2


def qr_code_decoder(file):
    img = cv2.imread(file)
    det = cv2.QRCodeDetector()
    val, pts, st_code = det.detectAndDecode(img)
    return val

# IT WORKS!
# qr_code_decoder("db/data/codes/637cb66371fb51264bef0bda.jpg")
