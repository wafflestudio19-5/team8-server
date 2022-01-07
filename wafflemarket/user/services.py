import os
import random
import string
from django.utils.timezone import now
 
def upload_image(instance, filename):
    filename_base, filename_ext = os.path.splitext(filename)

    return '%s' % (now().strftime('%Y%m%d%H%M%S')+'_'+''.join(random.choices(string.ascii_lowercase + string.digits, k=10)))

def upload_profile_image(instance, filename):
    return 'profile_image/'+upload_image(instance, filename)

def upload_product_image(instance, filename):
    return 'product_image/'+upload_image(instance, filename)