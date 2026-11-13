"""Independent device credentials; provider keys are never device credentials."""
import hashlib
import hmac
import re


def identify(value, legacy_hash, extra_hashes=None):
    if not isinstance(value, str) or not value or len(value) > 256:
        return None
    digest = hashlib.sha256(value.encode()).hexdigest()
    if isinstance(legacy_hash, str) and hmac.compare_digest(digest, legacy_hash):
        return 'tv-sdx43'
    if not isinstance(extra_hashes, dict) or len(extra_hashes) > 32:
        return None
    for device, expected in extra_hashes.items():
        if (isinstance(device, str) and re.fullmatch(r'[a-z0-9-]{1,48}', device)
                and isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected)
                and hmac.compare_digest(digest, expected)):
            return device
    return None
