import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image
import os


def qr_code_generator(_id):
    parent = os.path.dirname(os.getcwd())
    logo_path = os.path.join(parent, "database/logo.jpg")
    logo = Image.open(logo_path)

    # taking base width
    basewidth = 100
    # adjust image size
    wpercent = (basewidth/float(logo.size[0]))
    hsize = int((float(logo.size[1])*float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, version=2, border=1, box_size=12)
    qr.add_data(str(_id))
    qr_img = qr.make_image(image_factory=StyledPilImage,
                           color_mask=SolidFillColorMask())

    # set size of QR code
    pos = ((qr_img.size[0] - logo.size[0]) // 2,
           (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos)

    path = os.path.join(parent, "database/data/codes")
    filename = f"{path}/{str(_id)}.jpg"
    qr_img.save(filename)
    return filename


qr_code_generator(123456789123456789)