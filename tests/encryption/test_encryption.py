"""
Test script for API key encryption/decryption workflow
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.crypto_utils import CryptoManager, get_api_key


def test_encryption_workflow():
    """Test the complete encryption/decryption workflow"""
    print("Testing API Key Encryption Workflow\n")
    print("=" * 50)
    
    # Initialize CryptoManager
    crypto_mgr = CryptoManager()
    
    # Test 1: Check ADE-Crypt installation
    print("\n1. Checking ADE-Crypt installation...")
    result = subprocess.run(["which", "ade-crypt-lib"], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ ADE-Crypt is installed at:", result.stdout.strip())
    else:
        print("   ✗ ADE-Crypt not found. Please install it first.")
        return False
    
    # Test 2: Test encryption
    print("\n2. Testing encryption...")
    test_key_name = "TEST_API_KEY"
    test_key_value = "test_secret_key_12345"
    
    if crypto_mgr.encrypt_key(test_key_name, test_key_value):
        print(f"   ✓ Successfully encrypted {test_key_name}")
    else:
        print(f"   ✗ Failed to encrypt {test_key_name}")
        return False
    
    # Test 3: Test decryption
    print("\n3. Testing decryption...")
    decrypted_value = crypto_mgr.decrypt_key(test_key_name)
    
    if decrypted_value == test_key_value:
        print(f"   ✓ Successfully decrypted {test_key_name}")
        print(f"   ✓ Values match: original and decrypted are identical")
    else:
        print(f"   ✗ Decryption failed or values don't match")
        print(f"      Original: {test_key_value}")
        print(f"      Decrypted: {decrypted_value}")
        return False
    
    # Test 4: Test fallback to environment variable
    print("\n4. Testing environment variable fallback...")
    os.environ["FALLBACK_KEY"] = "fallback_value"
    fallback_value = get_api_key("NONEXISTENT_KEY", "FALLBACK_KEY")
    
    if fallback_value == "fallback_value":
        print("   ✓ Fallback to environment variable works")
    else:
        print("   ✗ Fallback failed")
        return False
    
    # Test 5: Test with actual API keys (if .env exists)
    print("\n5. Testing with actual API keys...")
    env_file = Path(".env")
    
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check for Claude API key
        claude_key = get_api_key("CLAUDE_API_KEY")
        if claude_key and not claude_key.startswith("your_"):
            print("   ✓ Claude API key accessible")
        else:
            print("   ⚠ Claude API key not configured or is placeholder")
        
        # Check for OpenAI API key
        openai_key = get_api_key("OPENAI_API_KEY")
        if openai_key and not openai_key.startswith("your_"):
            print("   ✓ OpenAI API key accessible")
        else:
            print("   ⚠ OpenAI API key not configured or is placeholder")
    else:
        print("   ⚠ .env file not found, skipping actual API key tests")
    
    # Clean up test file
    test_file = Path("./config/encrypted/TEST_API_KEY.enc")
    if test_file.exists():
        test_file.unlink()
        print("\n✓ Cleaned up test files")
    
    print("\n" + "=" * 50)
    print("✅ All encryption tests passed!")
    return True


def test_encryption_script():
    """Test the encryption setup script"""
    print("\n\nTesting Encryption Setup Script\n")
    print("=" * 50)
    
    script_path = Path("./scripts/encrypt-api-keys.sh")
    
    if not script_path.exists():
        print("✗ Encryption script not found at:", script_path)
        return False
    
    # Test script help
    print("\n1. Testing script help...")
    result = subprocess.run([str(script_path)], capture_output=True, text=True)
    if "Usage:" in result.stdout:
        print("   ✓ Script help works")
    else:
        print("   ✗ Script help failed")
        return False
    
    # Test verify command (won't have encrypted keys yet)
    print("\n2. Testing verify command...")
    result = subprocess.run([str(script_path), "verify"], capture_output=True, text=True)
    print("   ✓ Verify command runs (may show no encrypted keys)")
    
    print("\n" + "=" * 50)
    print("✅ Encryption script tests completed!")
    return True


if __name__ == "__main__":
    print("API Key Encryption Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run encryption workflow tests
    if not test_encryption_workflow():
        success = False
    
    # Run script tests
    if not test_encryption_script():
        success = False
    
    if success:
        print("\n🎉 All tests passed successfully!")
        print("\nNext steps:")
        print("1. Create a .env file with your actual API keys")
        print("2. Run: ./scripts/encrypt-api-keys.sh setup")
        print("3. Verify encryption: ./scripts/encrypt-api-keys.sh verify")
        print("4. Remove plain text keys from .env file")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    sys.exit(0 if success else 1)