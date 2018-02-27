import qrcode
import os


imgs_folder = os.path.abspath('app') + '\\QRcode\\imgs\\'
baseUrl = 'http://nami.slms.au.ngrok.io'
qr = qrcode.QRCode(version=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                   box_size=10,
                   border=4, )


def qr_generator(device_id):
    data = baseUrl + '/form' + str(device_id)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img.save(imgs_folder + 'Device {0}.png'.format(device_id))
