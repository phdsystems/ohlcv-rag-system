"""
Test script for simple Python-based encryption
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.simple_crypto import SimpleCrypto, SecureConfig, get_encrypted_api_key


def test_simple_crypto():
    """Test the simple crypto implementation"""
    print("Testing Simple Crypto Implementation\n")
    print("=" * 50)
    
    # Test 1: Basic encryption/decryption
    print("\n1. Testing basic encryption/decryption...")
    crypto = SimpleCrypto(key_file="./config/.test_key")
    
    test_string = "my_secret_api_key_12345"
    encrypted = crypto.encrypt(test_string)
    decrypted = crypto.decrypt(encrypted)
    
    if decrypted == test_string:
        print("   ✓ Basic encryption/decryption works")
        print(f"   ✓ Original: {test_string[:10]}...")
        print(f"   ✓ Encrypted: {encrypted[:20]}...")
    else:
        print("   ✗ Encryption/decryption failed")
        return False
    
    # Test 2: File encryption/decryption
    print("\n2. Testing file encryption/decryption...")
    test_file = Path("./config/encrypted/test_key.enc")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    crypto.encrypt_file(test_string, test_file)
    decrypted_from_file = crypto.decrypt_file(test_file)
    
    if decrypted_from_file == test_string:
        print("   ✓ File encryption/decryption works")
    else:
        print("   ✗ File encryption/decryption failed")
        return False
    
    # Test 3: SecureConfig
    print("\n3. Testing SecureConfig...")
    config = SecureConfig()
    
    # Set and get a key
    config.set_key("TEST_API_KEY", "test_value_123")
    retrieved = config.get_key("TEST_API_KEY")
    
    if retrieved == "test_value_123":
        print("   ✓ SecureConfig set/get works")
    else:
        print("   ✗ SecureConfig failed")
        return False
    
    # Test 4: Environment fallback
    print("\n4. Testing environment fallback...")
    os.environ["FALLBACK_TEST_KEY"] = "fallback_value"
    fallback_result = config.get_key("NONEXISTENT_KEY", "FALLBACK_TEST_KEY")
    
    if fallback_result == "fallback_value":
        print("   ✓ Environment fallback works")
    else:
        print("   ✗ Environment fallback failed")
        return False
    
    # Test 5: Encrypt from environment
    print("\n5. Testing encrypt from environment...")
    os.environ["TEST_CLAUDE_KEY"] = "sk-test-claude-key"
    os.environ["CLAUDE_API_KEY"] = "sk-test-claude-key"
    
    count = config.encrypt_from_env()
    print(f"   ✓ Encrypted {count} keys from environment")
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    Path("./config/encrypted/TEST_API_KEY.enc").unlink(missing_ok=True)
    Path("./config/.test_key").unlink(missing_ok=True)
    Path("./config/.encryption_key").unlink(missing_ok=True)
    
    print("\n" + "=" * 50)
    print("✅ All simple crypto tests passed!")
    return True


def test_integration():
    """Test integration with main crypto_utils"""
    print("\n\nTesting Integration with crypto_utils\n")
    print("=" * 50)
    
    from src.utils.crypto_utils import get_api_key
    
    # Set up a test key
    os.environ["TEST_INTEGRATION_KEY"] = "integration_test_value"
    
    # Test that get_api_key can retrieve it
    value = get_api_key("TEST_INTEGRATION_KEY")
    
    if value == "integration_test_value":
        print("   ✓ Integration with crypto_utils works")
    else:
        print("   ✗ Integration failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Integration test passed!")
    return True


if __name__ == "__main__":
    print("Simple Crypto Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run simple crypto tests
    if not test_simple_crypto():
        success = False
    
    # Run integration tests
    if not test_integration():
        success = False
    
    if success:
        print("\n🎉 All tests passed successfully!")
        print("\nThe system now supports two encryption methods:")
        print("1. ADE-Crypt (shell-based, if installed)")
        print("2. Python cryptography library (fallback)")
        print("\nTo use encrypted API keys:")
        print("1. Set your API keys in .env file")
        print("2. Run: python -c 'from src.utils.simple_crypto import get_secure_config; get_secure_config().encrypt_from_env()'")
        print("3. Your keys are now encrypted in ./config/encrypted/")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    sys.exit(0 if success else 1)