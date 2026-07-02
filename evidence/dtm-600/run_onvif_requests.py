#!/usr/bin/env python3
"""
Send a battery of ONVIF SOAP requests to the device SOAP endpoint on port 81
and save each response body to disk for later analysis.

The request payloads mirror the templates documented in soap-onvif-port81.md.
"""

import pathlib
import sys
from typing import Dict

import requests
from requests.auth import HTTPDigestAuth


BASE_URL = "http://192.168.30.178:81/onvif/device_service"
USERNAME = "admin"
PASSWORD = "admin"
OUTPUT_DIR = pathlib.Path("onvif_responses")

# Static payloads lifted from soap-onvif-port81.md; adjust tokens if the target
# uses different profile/config identifiers.
PAYLOADS: Dict[str, str] = {
    "GetServices": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetServices>
      <tds:IncludeCapability>true</tds:IncludeCapability>
    </tds:GetServices>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetCapabilities": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetCapabilities>
      <tds:Category>All</tds:Category>
    </tds:GetCapabilities>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetProfiles": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetProfiles/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetStreamUri": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl" xmlns:tt="http://www.onvif.org/ver10/schema">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetStreamUri>
      <trt:StreamSetup>
        <tt:Stream>RTP-Unicast</tt:Stream>
        <tt:Transport>
          <tt:Protocol>RTSP</tt:Protocol>
        </tt:Transport>
      </trt:StreamSetup>
      <trt:ProfileToken>media_profile1</trt:ProfileToken>
    </trt:GetStreamUri>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetDeviceInformation": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDeviceInformation/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetSystemDateAndTime": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemDateAndTime/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetNetworkInterfaces": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkInterfaces/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetUsers": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetUsers/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetHostname": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetHostname/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetDNS": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDNS/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetNetworkDefaultGateway": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkDefaultGateway/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetNetworkProtocols": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkProtocols/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetNTP": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNTP/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetDynamicDNS": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDynamicDNS/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetIPAddressFilter": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetIPAddressFilter/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetDiscoveryMode": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDiscoveryMode/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetScopes": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetScopes/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetRelayOutputs": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetRelayOutputs/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetSystemLog": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemLog>
      <tds:LogType>System</tds:LogType>
    </tds:GetSystemLog>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetSystemSupportInformation": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemSupportInformation/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetSystemBackup": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemBackup/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetSnapshotUri": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetSnapshotUri>
      <trt:ProfileToken>media_profile1</trt:ProfileToken>
    </trt:GetSnapshotUri>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetVideoEncoderConfigurations": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetVideoEncoderConfigurations/>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetOSDs": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetOSDs>
      <trt:ConfigurationToken>video_encoder_config</trt:ConfigurationToken>
      <trt:OSDToken/>
    </trt:GetOSDs>
  </soapenv:Body>
</soapenv:Envelope>""",
    "GetAnalyticsEngines": """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tan="http://www.onvif.org/ver20/analytics/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tan:GetAnalyticsEngines/>
  </soapenv:Body>
</soapenv:Envelope>""",
}


def main() -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    auth = HTTPDigestAuth(USERNAME, PASSWORD)
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
    }

    session = requests.Session()
    session.auth = auth

    print(f"[+] Target: {BASE_URL}")
    for name, body in PAYLOADS.items():
        # SOAPAction matters for routing; derive from action name when possible.
        if name.startswith("Get") and name not in {"GetAnalyticsEngines"}:
            if "media" in body:
                soap_action = f'"http://www.onvif.org/ver10/media/wsdl/{name}"'
            else:
                soap_action = f'"http://www.onvif.org/ver10/device/wsdl/{name}"'
        elif name == "GetAnalyticsEngines":
            soap_action = '"http://www.onvif.org/ver20/analytics/wsdl/GetAnalyticsEngines"'
        else:
            soap_action = ""

        local_headers = headers.copy()
        if soap_action:
            local_headers["SOAPAction"] = soap_action

        print(f"[+] Sending {name} ...", end="", flush=True)
        timeout = 70 if name in {"GetSystemLog", "GetSystemSupportInformation", "GetSystemBackup"} else 15
        resp = session.post(BASE_URL, data=body.encode("utf-8"), headers=local_headers, timeout=timeout)
        output_path = OUTPUT_DIR / f"{name}.xml"
        output_path.write_bytes(resp.content)
        print(f" status={resp.status_code}, saved {len(resp.content)} bytes -> {output_path}")

    print(f"[+] Complete. Responses stored in {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Aborted by user")
        sys.exit(1)
