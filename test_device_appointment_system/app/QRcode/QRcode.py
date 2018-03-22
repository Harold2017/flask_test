import qrcode
import os


def qr_generator(device_id):
    imgs_folder = os.path.abspath('app') + '/static/QRcode'
    if not os.path.exists(imgs_folder):
        os.makedirs(imgs_folder)
    baseUrl = 'http://www.namihk.com'
    qr = qrcode.QRCode(version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4, )
    data = baseUrl + '/form/' + str(device_id)
    # data = 'http://www.namihk.com/form/' + str(device_id)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img.save(imgs_folder + '/Device{0}.png'.format(device_id))
    del qr
    del data
    del img
