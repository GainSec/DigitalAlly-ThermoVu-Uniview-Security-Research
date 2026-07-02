# Excluded From Public Release

The public tree intentionally excludes:

- Git/workspace internals: `.git/`, `.work/`, `.DS_Store`, local rebase state, askpass helpers.
- Agent/private workflow files: `AGENTS.MD`, `CLAUDE.md`.
- Local Python environments and caches: `.venv/`, nested `venv/`, `__pycache__/`, `*.pyc`.
- Private/local secret carriers: `.env` files, private key material, local credential helpers.
- Personal biometric inputs and derivatives: `my_face_from_device.jpg`, enrolled face images, remote `FACE_MUTATIONS` images, and local morph/adversarial image sets derived from personal face inputs.
- Oversized/raw artifacts: firmware dumps, raw `program.bin`/`*.bin.data`, large tar/zip firmware packages, compressed diagnostic/log bundles, software installer archives, APK/EXE payloads, dump tarballs, and Burp project databases.
- Raw firmware/module fragments from the extracted filesystem. Small generated template blobs and extracted FaceID template blobs are retained as research test/evidence artifacts.
- Duplicates from the older CVE repo when the local repo already had the same artifact.

Target-derived product evidence was kept when it was small enough and useful for review, including configs, passwd/hash evidence, target certificates, ONVIF XML, diagnostic logs, web assets, scripts, and extracted firmware filesystem content.
