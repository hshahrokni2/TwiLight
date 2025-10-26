#!/usr/bin/env python3
"""
Test script to verify TELEGRAM_USER_ID validation fix
Tests different scenarios:
1. TELEGRAM_USER_ID not set → use default
2. TELEGRAM_USER_ID = 'your_telegram_user_id' → use default
3. TELEGRAM_USER_ID = '123456789' → use that value
4. TELEGRAM_USER_ID = '' → use default
5. TELEGRAM_USER_ID = 'invalid123abc' → use default
"""

import os
import sys

# Test the safe_int_conversion function
from config_loader import safe_int_conversion, load_config

def test_safe_int_conversion():
    print("Testing safe_int_conversion function...")
    print("-" * 50)
    
    # Test 1: Valid numeric string
    result = safe_int_conversion("123456789", 7171577450)
    assert result == 123456789, f"Test 1 failed: Expected 123456789, got {result}"
    print("✅ Test 1: Valid numeric string '123456789' → 123456789")
    
    # Test 2: Invalid placeholder string
    result = safe_int_conversion("your_telegram_user_id", 7171577450)
    assert result == 7171577450, f"Test 2 failed: Expected 7171577450, got {result}"
    print("✅ Test 2: Placeholder 'your_telegram_user_id' → 7171577450 (default)")
    
    # Test 3: Empty string
    result = safe_int_conversion("", 7171577450)
    assert result == 7171577450, f"Test 3 failed: Expected 7171577450, got {result}"
    print("✅ Test 3: Empty string '' → 7171577450 (default)")
    
    # Test 4: Mixed alphanumeric
    result = safe_int_conversion("abc123def", 7171577450)
    assert result == 7171577450, f"Test 4 failed: Expected 7171577450, got {result}"
    print("✅ Test 4: Invalid 'abc123def' → 7171577450 (default)")
    
    # Test 5: Negative number (valid for group_chat_id)
    result = safe_int_conversion("-4800163944", -4800163944)
    assert result == -4800163944, f"Test 5 failed: Expected -4800163944, got {result}"
    print("✅ Test 5: Negative number '-4800163944' → -4800163944")
    
    # Test 6: Whitespace with number
    result = safe_int_conversion("  987654321  ", 7171577450)
    assert result == 987654321, f"Test 6 failed: Expected 987654321, got {result}"
    print("✅ Test 6: Whitespace '  987654321  ' → 987654321")
    
    print("-" * 50)
    print("✅ ALL TESTS PASSED!")
    return True

def test_config_loading():
    print("\nTesting config loading with different TELEGRAM_USER_ID values...")
    print("-" * 50)
    
    # Save original env var
    original_value = os.environ.get('TELEGRAM_USER_ID')
    original_db = os.environ.get('DATABASE_URL')
    
    # Set a minimal DATABASE_URL for testing
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
    
    try:
        # Test scenario 1: Invalid placeholder
        os.environ['TELEGRAM_USER_ID'] = 'your_telegram_user_id'
        config = load_config()
        user_id = config['telegram']['user_id']
        assert user_id == 7171577450, f"Scenario 1 failed: Expected 7171577450, got {user_id}"
        print("✅ Scenario 1: Placeholder value → Uses default (7171577450)")
        
        # Test scenario 2: Valid numeric ID
        os.environ['TELEGRAM_USER_ID'] = '999888777'
        config = load_config()
        user_id = config['telegram']['user_id']
        assert user_id == 999888777, f"Scenario 2 failed: Expected 999888777, got {user_id}"
        print("✅ Scenario 2: Valid numeric '999888777' → Uses that value (999888777)")
        
        # Test scenario 3: Empty string
        os.environ['TELEGRAM_USER_ID'] = ''
        config = load_config()
        user_id = config['telegram']['user_id']
        assert user_id == 7171577450, f"Scenario 3 failed: Expected 7171577450, got {user_id}"
        print("✅ Scenario 3: Empty string → Uses default (7171577450)")
        
        # Test scenario 4: Not set (deleted from env)
        if 'TELEGRAM_USER_ID' in os.environ:
            del os.environ['TELEGRAM_USER_ID']
        config = load_config()
        user_id = config['telegram']['user_id']
        assert user_id == 7171577450, f"Scenario 4 failed: Expected 7171577450, got {user_id}"
        print("✅ Scenario 4: Not set → Uses default (7171577450)")
        
    finally:
        # Restore original env var
        if original_value is not None:
            os.environ['TELEGRAM_USER_ID'] = original_value
        elif 'TELEGRAM_USER_ID' in os.environ:
            del os.environ['TELEGRAM_USER_ID']
            
        if original_db is not None:
            os.environ['DATABASE_URL'] = original_db
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    print("-" * 50)
    print("✅ ALL CONFIG LOADING TESTS PASSED!")
    return True

if __name__ == "__main__":
    try:
        test_safe_int_conversion()
        test_config_loading()
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS SUCCESSFUL!")
        print("=" * 50)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
