import qrcode
from utils.globalvar import SERVER_URL
from uuid import uuid1


def generate_qrcode(content: str, qr_code_name: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    qr_code = qr.make_image(fill_color="black", back_color="white")
    qr_code.save(f"static/{qr_code_name}.png")
    qr_code_url = f"{SERVER_URL}/static/{qr_code_name}.png"
    return qr_code_url



