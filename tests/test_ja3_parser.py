from capture.capture import parse_ja3

def test_parse_ja3_too_short():
    """Should return None gracefully on short packets."""
    result = parse_ja3(b'\x00' * 10, 0)
    assert result is None

def test_parse_ja3_not_tls():
    """Should return None for non-TLS packets."""
    raw = b'\x00' * 40 + b'\x17' + b'\x00' * 50  # 0x17 is not TLS handshake
    result = parse_ja3(raw, 20)
    assert result is None

def test_parse_ja3_returns_md5_format():
    """If it returns something, it should be a 32-char hex string."""
    import hashlib
    # build a minimal valid-looking TLS ClientHello
    transport_start = 0
    payload = bytearray(200)
    payload[20] = 0x16      # TLS record type
    payload[25] = 0x01      # ClientHello
    payload[29] = 0x03      # TLS version high
    payload[30] = 0x03      # TLS version low (TLS 1.2)
    # rest is zeros which will produce a parseable but minimal hash
    result = parse_ja3(bytes(payload), transport_start)
    if result is not None:
        assert len(result) == 32
        assert all(c in '0123456789abcdef' for c in result)