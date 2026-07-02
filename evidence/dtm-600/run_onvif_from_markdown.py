#!/usr/bin/env python3
"""
Parse the soap-onvif-port81.md playbook and execute every ONVIF SOAP request
defined there, saving each response for analysis.
"""

import pathlib
import re
import sys
from typing import Dict, Tuple

import requests
from requests.auth import HTTPDigestAuth


MD_PATH = pathlib.Path("soap-onvif-port81.md")
OUTPUT_DIR = pathlib.Path("onvif_responses_markdown")
USERNAME = "admin"
PASSWORD = "admin"

SECTION_RE = re.compile(r"^###\s+(?P<label>.+?)\n```(?:\w+)?\n(?P<raw>.+?)```", re.MULTILINE | re.DOTALL)


def parse_http_block(block: str) -> Tuple[str, str, Dict[str, str], str]:
    """
    Convert a raw HTTP request block (method, headers, blank line, body) into
    components usable with requests.
    """
    if "\n\n" not in block:
        raise ValueError("HTTP block missing separating blank line between headers and body")

    header_part, body_part = block.split("\n\n", 1)
    header_lines = header_part.splitlines()
    if not header_lines:
        raise ValueError("HTTP block missing request line")

    request_line = header_lines[0].strip()
    try:
        method, path, _ = request_line.split()
    except ValueError as exc:
        raise ValueError(f"Unable to parse request line: {request_line}") from exc

    headers: Dict[str, str] = {}
    for line in header_lines[1:]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Malformed header line: {line}")
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    # Remove Content-Length so requests can recalculate.
    headers.pop("Content-Length", None)
    return method.upper(), path, headers, body_part


def main() -> int:
    if not MD_PATH.exists():
        print(f"[!] Markdown source {MD_PATH} not found", file=sys.stderr)
        return 1

    text = MD_PATH.read_text(encoding="utf-8")
    sections = list(SECTION_RE.finditer(text))
    if not sections:
        print("[!] No request sections found in markdown", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    session = requests.Session()
    session.auth = HTTPDigestAuth(USERNAME, PASSWORD)

    for match in sections:
        label = match.group("label").strip()
        raw_http = match.group("raw").strip()
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)

        try:
            method, path, headers, body = parse_http_block(raw_http)
        except ValueError as exc:
            print(f"[!] Skipping {label}: {exc}", file=sys.stderr)
            continue

        host = headers.get("Host")
        if not host:
            print(f"[!] Skipping {label}: Host header missing", file=sys.stderr)
            continue

        scheme = "http"
        if host.endswith(":443"):
            scheme = "https"

        url = f"{scheme}://{host}{path}"

        print(f"[+] {label} -> {url}")
        timeout = 70 if "GetSystemLog" in label or "GetSystemSupportInformation" in label or "GetSystemBackup" in label else 15
        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                data=body.encode("utf-8"),
                timeout=timeout,
            )
        except requests.RequestException as exc:
            print(f"[!] Request {label} failed: {exc}", file=sys.stderr)
            continue

        output_path = OUTPUT_DIR / f"{safe_label}.xml"
        output_path.write_bytes(response.content)
        print(f"    status={response.status_code}, bytes={len(response.content)}, saved={output_path}")

    print(f"[+] Completed. Responses saved under {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Aborted by user")
        sys.exit(1)
