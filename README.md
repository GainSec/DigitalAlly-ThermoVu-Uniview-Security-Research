# Digital Ally ThermoVu DTM-600 Research Release

Public release package for independent security research on the Digital Ally ThermoVu DTM-600 facial-recognition and thermal access-control device. The device analyzed in this release is a Uniview/OEM OET-213H-NB-family target running HiSilicon firmware with LAPI, ONVIF/SOAP, RTSP, PACS/access-control, and local face-template storage surfaces.

This repository keeps the useful documentation, findings, evidence summaries, source tools, generated test artifacts, and selected device-derived evidence while excluding local workflow state, raw oversized firmware/software archives, private agent instructions, virtual environments, Burp project databases, and personal biometric source images.

## Target

| Field | Value |
|-------|-------|
| Research target | Digital Ally ThermoVu DTM-600 |
| OEM / platform family | Uniview OET-213H-NB / OET-213H-NB-WH |
| Device class | Facial-recognition and thermal access-control terminal |
| OEM vendor | Zhejiang Uniview Technologies |
| SoC | HiSilicon Hi3516DV300-class ARMv7 platform |
| Architecture | Dual-core ARM Cortex-A7, ARMv7 |
| Kernel observed | Linux 4.9.37 |
| Main firmware branch observed | `QPTS-B2209.3.70.CEN001.200707` |
| Main application | `mwareserver` |
| Web/API surface | HTTP web UI, Uniview LAPI REST endpoints, ONVIF/SOAP on port 81 |
| Media/control surface | RTSP, SDK/proprietary service, PACS/face-recognition APIs |
| Research focus | Remote compromise chain, exposed management services, hardcoded credentials, ONVIF/LAPI exposure, and face-template authentication weaknesses |

## Repository Map

| Path | What it contains |
|------|------------------|
| `NOTES/` | Findings, leads, runtime notes, LAPI reference, face-template research, shell escape notes, and PoC support files. |
| `docs/` | Root-level reports, exploit-chain summary, U-Boot/network plans, and generated finding text. |
| `evidence/` | Curated diagnostic extracts, ONVIF responses, selected firmware filesystem content, configs, logs, and device-derived proof material. |
| `test-artifacts/` | Generated fuzz corpora, synthetic image candidates, template candidates, extracted embedding-analysis outputs, and sanitized import CSVs. |
| `tools/` | DTM-600-focused helper tools retained with the research release. |
| `standalone/uniview-lapi-toolkit/` | Separately releasable Uniview/OEM LAPI endpoint browser and request client. |
| `SCRIPTS/` | Research scripts for image, morphing, adversarial, runtime, and template-analysis workflows. |
| `vendor-docs/` | Public product documentation copied into the release for context. |
| `remote-cve-snapshot/` | Small unique artifacts from the related `digitalally-facialrec` repository snapshot. |
| `RELEASE_INVENTORY.txt` | File inventory for this public release tree. |
| `SHA256SUMS.txt` | SHA-256 hashes for release artifacts. |

## Vulnerability Summary

| ID | Title | Severity / CVSS | CWE / Class | Short description |
|----|-------|-----------------|-------------|-------------------|
| VULN-001 | Pre-authentication RCE via UDP/7788 | Critical, 9.8 | CWE-120 / memory corruption | Undocumented UDP service on port 7788 can be abused to spawn a Telnet service and gain root-level access. |
| VULN-002 | Default Telnet root credentials | Critical, 9.8 | CWE-798 | Telnet accepts static root credentials when exposed, leading to root shell access. |
| VULN-003 | Restricted shell escape via `updatecpld` | High, 8.8 | CWE-78 / unsafe command path | Restricted `uvsh` access can be escalated to an unrestricted root shell through FTP-fetched executable content. |
| VULN-004 | Hardcoded web/admin and service credentials | High, 7.4-8.8 | CWE-798 / CWE-522 | Device configs contain default web, PPPoE, Wi-Fi, PTZ, NAS, and service credential material. |
| VULN-005 | Weak DES password hash in `/etc/passwd` | High, 7.8 | CWE-328 | Root credential material is stored with legacy DES crypt behavior instead of modern shadowed password storage. |
| VULN-006 | Hardcoded super-password / recovery credential | High, 8.8 | CWE-798 / authentication bypass | Configuration includes a static super-password mechanism that can unlock privileged/debug behavior. |
| VULN-007 | Shared expired TLS certificate and private key | High, 8.6 | CWE-321 / CWE-295 | Device-derived evidence includes an expired Uniview certificate bundled with private key material. |
| VULN-008 | Web API can enable Telnet remotely | High, 8.8 | CWE-284 | LAPI exposes Telnet/debug service control, turning credential compromise into persistent shell exposure. |
| VULN-009 | Large LAPI management attack surface | Medium to Critical depending on auth bypass | API authorization / attack surface | More than 200 LAPI endpoints cover factory reset, firmware update, user management, debug controls, media, face, and PACS actions. |
| VULN-010 | ActiveX web plugin exposure | High, 7.5 | Client-side attack surface | Legacy web UI components reference ActiveX/plugin installers and hardcoded CLSIDs for browser-side video controls. |
| VULN-011 | Debug page with hardcoded external IP reference | Medium, 4.0 | Information disclosure | Debug HTML contains a hardcoded external address and remote flag that should not ship in production firmware. |
| VULN-012 | Face-template injection / identity mismatch | High after filesystem access | Authentication design flaw | Stored photos and matching templates are separate artifacts, allowing a displayed identity to differ from the biometric template used for matching. |
| VULN-013 | Zero-template face-recognition bypass | High after filesystem access | Input validation / numeric edge case | Replacing template vectors with zero-valued embeddings caused successful face matches in testing, consistent with missing vector-magnitude validation. |

Finding detail lives in:

- `NOTES/findingslist.md`
- `NOTES/telnet-findings.md`
- `docs/full-chain.md`
- `NOTES/shell-escape.md`
- `NOTES/LAPI.md`
- `NOTES/template-injection-bypass.md`
- `NOTES/CVE-zero-template-bypass.md`
- `NOTES/runtime-enumeration.md`

## Confirmed Attack Chain

The main demonstrated compromise path combines the network RCE and restricted-shell escape:

1. Reach vulnerable UDP/7788 maintenance service.
2. Trigger Telnet exposure through the known Uniview maintenance overflow path.
3. Authenticate to the restricted vendor shell through default/root access.
4. Use the `updatecpld` FTP execution path to run attacker-controlled content.
5. Obtain unrestricted root shell and full device control.

The detailed chain and cleanup notes are documented in `docs/full-chain.md`, `NOTES/telnet-findings.md`, and `NOTES/shell-escape.md`.

## Attack Surface

| Surface | Details |
|---------|---------|
| UDP maintenance service | UDP/7788 service associated with the known Uniview maintenance overflow path. |
| Telnet | Telnet service can be exposed by exploit chain or debug controls and leads to restricted or unrestricted shell access depending on path. |
| HTTP web UI | Web management interface served by `mwareserver`; includes LAPI-backed configuration and legacy browser/plugin behavior. |
| LAPI REST API | System, auth, network, firmware, debug, media, smart analytics, face-recognition, PACS, I/O, and traffic/intelligence endpoints. |
| ONVIF/SOAP | ONVIF service and response captures on port 81, including device, media, network, users, scopes, profiles, snapshots, and system backup calls. |
| RTSP/media | RTSP streaming and snapshot/media paths exposed by the device firmware. |
| SDK/proprietary service | Runtime enumeration identified a proprietary service on high TCP ports for vendor/client integration. |
| PACS/access control | Door/gate, Wiegand, QR, temperature, verification-template, and controller status functionality. |
| Face-template storage | Face photos and binary matching templates stored separately under `/data/WorkLibFile/...`. |
| Local firmware/config storage | `/config`, `/program`, `/data`, diagnostic bundles, web assets, certificates, and runtime logs. |

## Tool Suite

| Tool / area | Path | Purpose |
|-------------|------|---------|
| DTM-600 LAPI helpers | `tools/lapi_cli.py`, `tools/lapi_interactive.py` | Project-specific LAPI endpoint testing and browsing for the DTM-600 target. |
| Standalone LAPI toolkit | `standalone/uniview-lapi-toolkit/` | Generic Uniview/OEM LAPI endpoint browser and request client suitable for separate release. |
| ONVIF replay/execution helpers | `evidence/dtm-600/run_onvif_requests.py`, `evidence/dtm-600/run_onvif_from_markdown.py` | Replay curated ONVIF/SOAP requests and collect responses. |
| UDP/7788 support material | `evidence/dtm-600/exploit_udp_7788.py`, `NOTES/reqs/poc_udp_7788_overflow.py` | Research PoC and support scripts for the maintenance-service RCE chain. |
| Shell escape support | `NOTES/reqs/cpldload`, `NOTES/reqs/cpldload_telnetd.sh`, `NOTES/reqs/poc_uvsh_escape.sh` | Controlled lab payloads and repro support for `updatecpld` behavior. |
| Face/template research scripts | `SCRIPTS/`, `remote-cve-snapshot/SCRIPTS/` | Template analysis, fuzz corpus generation, image mutation, and adversarial/research workflows. |
| Generated test artifacts | `test-artifacts/` | Candidate images, template payloads, fuzzing corpora, embedding analysis outputs, and import CSVs. |

## Standalone Uniview LAPI Toolkit

`standalone/uniview-lapi-toolkit/` is intended to be releasable independently from this DTM-600 evidence bundle. It includes:

- a generic `lapi_toolkit.py` client
- `generic-uniview` and `dtm600-validated` endpoint profiles
- a standalone README
- offline tests
- no hard-coded target address
- no hard-coded default credentials
- read-only behavior by default, with explicit flags required for writes

Use it as a starting point for authorized testing of Uniview and OEM devices that expose `/LAPI/...` endpoints. Endpoint availability varies by model, firmware branch, feature license, and OEM branding.

## Evidence And Reports

| Path | Use |
|------|-----|
| `evidence/dtm-600/onvif_responses/` | Captured ONVIF/SOAP responses from the target. |
| `evidence/dtm-600/onvif_responses_markdown/` | Responses generated from the markdown ONVIF playbook. |
| `evidence/dtm-600/diag_*` | Diagnostic configs, logs, ACS data, and runtime material. |
| `evidence/dtm-600/program_factory/` | Selected extracted firmware/web files needed for traceability and endpoint analysis. |
| `NOTES/reqs/` | Reproducer support files, hashes, scripts, cert material, and controlled lab payloads. |
| `test-artifacts/EXTRACTED_TEMPLATES/` | Sanitized embedding-analysis outputs retained after removing raw per-person template directories. |
| `test-artifacts/CANDIDATE_TEMPLATES/` | Synthetic template payloads used for robustness testing. |
| `test-artifacts/FUZZ_CORPUS/` | JPEG and metadata fuzzing corpus artifacts. |
| `vendor-docs/` | Product manuals and installation guides. |

## Exclusions

The public tree intentionally excludes:

- Raw oversized firmware dumps and installer/archive inputs.
- Local `.work/`, virtual environments, editor state, and private automation files.
- `AGENTS.MD`, `CLAUDE.md`, and private agent workflow instructions.
- Personal biometric source images and locally derived personal face images.
- Burp project databases and private local capture workspaces.
- Oversized raw artifacts that are not needed for public review.
- API keys, personal secrets, `.env` files, private local keys, and local machine-specific credentials.

Target-derived evidence is retained where it is part of the researched product or firmware, including configs, hashes, certificates, passwd-like files, and device-derived credential material. Those artifacts are included for reproducibility and should be handled as sensitive research evidence.

See `EXCLUDED_FROM_RELEASE.md` for the main excluded categories.

## Quick Checks

From the repository root, these should not list private workflow files, raw oversized inputs, or removed marker/person-template directories:

```bash
find . -name AGENTS.md -o -name AGENTS.MD -o -name CLAUDE.md -o -name '.env'
find . -type d \( -name '.work' -o -name '.venv' -o -name 'venv' \) -print
find . -type d \( -name 'MARKER_BYPASS' -o -name 'PersonID_*' \) -print
find . -type f \( -name '*.img' -o -name '*.iso' -o -name '*.qcow2' -o -name '*.vmdk' \) -print
shasum -a 256 -c SHA256SUMS.txt
```

## Integrity

`RELEASE_INVENTORY.txt` lists files included in this public tree. `SHA256SUMS.txt` contains SHA-256 hashes for release artifacts. The release tree is structured so a reviewer can identify what was included, what was deliberately excluded, and where each major finding is documented.

## Research Boundaries

This package is for authorized security research, vendor disclosure, reproducibility, and defensive review. It is not a general-purpose exploitation package and should not be used against devices or networks without permission.
