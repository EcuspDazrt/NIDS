import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.inference import ja3_is_malicious, load_ja3_blocklist

def test_blocklist_loads():
    blocklist = load_ja3_blocklist()
    print(f"Loaded {len(blocklist)} hashes")
    assert len(blocklist) > 0, "Blocklist is empty"
    print("PASS: blocklist loads correctly")

def test_known_malicious():
    # Dridex — one of the highest-volume entries in the list
    dridex_hash = "51c64c77e60f3980eea90869b68c58a8"
    result = ja3_is_malicious(dridex_hash)
    assert result == 1, f"Expected 1 for known Dridex hash, got {result}"
    print("PASS: known malicious hash correctly detected")

def test_known_benign():
    # made-up hash not in any blocklist
    fake_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    result = ja3_is_malicious(fake_hash)
    assert result == 0, f"Expected 0 for unknown hash, got {result}"
    print("PASS: unknown hash correctly returns 0")

def test_none_input():
    result = ja3_is_malicious(None)
    assert result == 0, f"Expected 0 for None input, got {result}"
    print("PASS: None input correctly returns 0")

def test_trickbot():
    trickbot_hash = "8916410db85077a5460817142dcbc8de"
    result = ja3_is_malicious(trickbot_hash)
    assert result == 1, f"Expected 1 for known TrickBot hash, got {result}"
    print("PASS: TrickBot hash correctly detected")

if __name__ == '__main__':
    test_blocklist_loads()
    test_known_malicious()
    test_known_benign()
    test_none_input()
    test_trickbot()
    print("\nAll tests passed.")