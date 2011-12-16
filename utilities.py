import re
def ip2long(ip):
    if ip is None or not testip(ip):
        return None
    (o1, o2, o3, o4) = ip.split('.')
    return ((int(o1) * 16777216) + (int(o2) * 65536) + \
                (int(o3) * 256) + int(o4))

def long2ip(long):
    if long is None or not re.match("^\d+$", str(long)):
        return None
    o1 = long / 2**(8*3)
    long -= (o1 * 2**(8*3))
    o2 = long / 2**(8*2)
    long -= (o2 * 2**(8*2))
    o3 = long / 2**8
    o4 = long - (o3 * 2**8)
    return ("%d.%d.%d.%d" % (o1, o2, o3, o4))

