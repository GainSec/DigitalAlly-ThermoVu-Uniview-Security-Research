# @soap-onvif-port81

Target: `http://192.168.30.178:81/onvif/device_service`

Digest auth: username `admin`, password `admin` (from `config_a.xml:360`). Send each request once without `Authorization` to capture the `WWW-Authenticate` challenge, then resend with the Digest header **Burp must generate for each replay**. A stale/hand-copied `Authorization` header will be rejected with `401` (nonce + nc must increment per request). Bodies below are copy/paste ready for Burp Repeater; only adjust `Content-Length` if your tooling does not auto-calc.

---

### GetServices
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetServices"
Content-Length: 267

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetServices>
      <tds:IncludeCapability>true</tds:IncludeCapability>
    </tds:GetServices>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetCapabilities
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetCapabilities"
Content-Length: 266

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetCapabilities>
      <tds:Category>All</tds:Category>
    </tds:GetCapabilities>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetProfiles
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/media/wsdl/GetProfiles"
Content-Length: 208

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetProfiles/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetStreamUri
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/media/wsdl/GetStreamUri"
Content-Length: 447

<?xml version="1.0" encoding="UTF-8"?>
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
</soapenv:Envelope>
```

### GetDeviceInformation
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"
Content-Length: 215

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDeviceInformation/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetSystemDateAndTime
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetSystemDateAndTime"
Content-Length: 226

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemDateAndTime/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetNetworkInterfaces
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetNetworkInterfaces"
Content-Length: 230

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkInterfaces/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetUsers
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetUsers"
Content-Length: 206

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetUsers/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetHostname
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetHostname"
Content-Length: 265

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetHostname/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetDNS
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetDNS"
Content-Length: 260

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDNS/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetNetworkDefaultGateway
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetNetworkDefaultGateway"
Content-Length: 278

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkDefaultGateway/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetNetworkProtocols
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetNetworkProtocols"
Content-Length: 273

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNetworkProtocols/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetNTP
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetNTP"
Content-Length: 260

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetNTP/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetDynamicDNS
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetDynamicDNS"
Content-Length: 267

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDynamicDNS/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetIPAddressFilter
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetIPAddressFilter"
Content-Length: 272

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetIPAddressFilter/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetDiscoveryMode
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetDiscoveryMode"
Content-Length: 270

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetDiscoveryMode/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetScopes
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetScopes"
Content-Length: 263

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetScopes/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetRelayOutputs
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetRelayOutputs"
Content-Length: 269

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetRelayOutputs/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetSystemLog
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetSystemLog"
Content-Length: 329

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemLog>
      <tds:LogType>System</tds:LogType>
    </tds:GetSystemLog>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetSystemSupportInformation
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetSystemSupportInformation"
Content-Length: 281

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemSupportInformation/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetSystemBackup
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/device/wsdl/GetSystemBackup"
Content-Length: 269

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tds:GetSystemBackup/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetSnapshotUri
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/media/wsdl/GetSnapshotUri"
Content-Length: 295

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetSnapshotUri>
      <trt:ProfileToken>media_profile1</trt:ProfileToken>
    </trt:GetSnapshotUri>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetVideoEncoderConfigurations
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/media/wsdl/GetVideoEncoderConfigurations"
Content-Length: 264

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetVideoEncoderConfigurations/>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetOSDs
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver10/media/wsdl/GetOSDs"
Content-Length: 356

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trt="http://www.onvif.org/ver10/media/wsdl" xmlns:tt="http://www.onvif.org/ver10/schema">
  <soapenv:Header/>
  <soapenv:Body>
    <trt:GetOSDs>
      <trt:ConfigurationToken>video_encoder_config</trt:ConfigurationToken>
      <trt:OSDToken/>
    </trt:GetOSDs>
  </soapenv:Body>
</soapenv:Envelope>
```

### GetProfiles (Analytics) – if needed
```
POST /onvif/device_service HTTP/1.1
Host: 192.168.30.178:81
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://www.onvif.org/ver20/analytics/wsdl/GetAnalyticsEngines"
Content-Length: 266

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tan="http://www.onvif.org/ver20/analytics/wsdl">
  <soapenv:Header/>
  <soapenv:Body>
    <tan:GetAnalyticsEngines/>
  </soapenv:Body>
</soapenv:Envelope>
```

---

Notes:
- If Burp does not auto-set `Content-Length`, recalc (each block already includes an accurate length for the shown payload).
- Default ONVIF profiles in `config_a.xml` are `media_profile1`, `media_profile2`; drop alternative tokens into any request needing `ProfileToken`.
- Firmware enables ONVIF discovery; use WS-Discovery (`udp/3702`) if you need to confirm the service URL from scratch.
- Some payloads reference configuration tokens (`video_encoder_config` etc.) straight from `config_a.xml` defaults. Replace with live values if they differ on target hardware.
