from xknx import XKNX
from xknx.io.async import GatewayScanner

xknx = XKNX()

gatewayscanner = GatewayScanner(xknx)
gatewayscanner.start()

if gatewayscanner.found:
    print("Gateway at: {0}:{1} ({2})".format(
        gatewayscanner.found_ip_addr,
        gatewayscanner.found_port,
        gatewayscanner.found_name))
else:
    print("No Gateways found")
