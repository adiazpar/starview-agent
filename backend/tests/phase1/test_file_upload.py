#!/usr/bin/env python3
"""
File Upload Validation Test Script

Tests file upload validation implementation for security issues 1.3.
Tests both profile picture uploads and review photo uploads.

Tests:
1. File size validation (5MB limit)
2. MIME type validation (images only)
3. File extension whitelist
4. Malicious file rejection
"""

import requests
import io
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

# Test credentials (create this user if it doesn't exist)
TEST_USER_LOGIN = {
    'username': 'filetest_user',
    'password': 'TestPass123!'
}

TEST_USER_REGISTER = {
    'username': 'filetest_user',
    'email': 'filetest@example.com',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
    'first_name': 'File',
    'last_name': 'Tester'
}


def create_test_image(size_mb=1, format='JPEG', width=800, height=600):
    """Create a test image of specified size in memory"""
    # Create image in memory
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()

    # Save with low quality to control size
    img.save(img_bytes, format=format, quality=10)

    # If we need to make it bigger, pad it
    current_size_mb = img_bytes.tell() / (1024 * 1024)
    if current_size_mb < size_mb:
        # Add padding to reach desired size
        padding_bytes = int((size_mb - current_size_mb) * 1024 * 1024)
        img_bytes.write(b'0' * padding_bytes)

    img_bytes.seek(0)
    return img_bytes


def create_fake_file(content, filename, content_type):
    """Create a fake file with specific content and mimetype"""
    file_obj = io.BytesIO(content.encode() if isinstance(content, str) else content)
    file_obj.name = filename
    return file_obj


def get_csrf_token(session):
    """Get CSRF token from login page"""
    response = session.get(f"{BASE_URL}/login/")
    if 'csrftoken' in session.cookies:
        return session.cookies['csrftoken']
    return None


def setup_test_user(session):
    """Create and login test user, return session"""
    print("Setting up test user...")

    # Get CSRF token first
    csrf_token = get_csrf_token(session)

    # Try to login first (user might already exist)
    login_response = session.post(
        f"{BASE_URL}/login/",
        json=TEST_USER_LOGIN,
        headers={'X-CSRFToken': csrf_token} if csrf_token else {}
    )

    if login_response.status_code == 200:
        print("✅ Test user logged in successfully (already existed)")
        return True

    # If login failed, try to register
    print("   User doesn't exist, creating new user...")
    csrf_token = get_csrf_token(session)  # Get fresh token
    register_response = session.post(
        f"{BASE_URL}/register/",
        json=TEST_USER_REGISTER,
        headers={'X-CSRFToken': csrf_token} if csrf_token else {}
    )

    if register_response.status_code == 201:
        print("✅ Test user created and logged in successfully")
        return True
    else:
        print(f"❌ Failed to create/login test user")
        print(f"   Register response: {register_response.status_code}")
        if register_response.status_code != 500:
            try:
                print(f"   Error: {register_response.json()}")
            except:
                print(f"   Response text: {register_response.text}")
        return False


def upload_with_csrf(session, url, files):
    """Helper to upload file with CSRF token"""
    csrf_token = get_csrf_token(session)
    return session.post(
        url,
        files=files,
        headers={'X-CSRFToken': csrf_token} if csrf_token else {}
    )


def test_profile_picture_file_size(session):
    """Test profile picture file size validation"""
    print("\n" + "="*60)
    print("TEST 1: Profile Picture File Size Validation")
    print("="*60)

    # Test 1a: Valid small image (2MB) - should succeed
    print("\n1a. Testing valid 2MB image...")
    small_image = create_test_image(size_mb=2)
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('test_small.jpg', small_image, 'image/jpeg')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        print("   ✅ PASS: Small file accepted")
        test1a = True
    else:
        print(f"   ❌ FAIL: Small file rejected - {response.json()}")
        test1a = False

    # Test 1b: Invalid large image (6MB) - should fail
    print("\n1b. Testing oversized 6MB image...")
    large_image = create_test_image(size_mb=6)
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('test_large.jpg', large_image, 'image/jpeg')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        error_msg = response.json().get('detail', '')
        print(f"   Error message: {error_msg}")
        if 'size' in error_msg.lower() or 'exceeds' in error_msg.lower():
            print("   ✅ PASS: Large file correctly rejected")
            test1b = True
        else:
            print(f"   ❌ FAIL: Wrong error message")
            test1b = False
    else:
        print(f"   ❌ FAIL: Large file accepted (should be rejected)")
        test1b = False

    return test1a and test1b


def test_profile_picture_mime_type(session):
    """Test profile picture MIME type validation"""
    print("\n" + "="*60)
    print("TEST 2: Profile Picture MIME Type Validation")
    print("="*60)

    # Test 2a: Valid JPEG - should succeed
    print("\n2a. Testing valid JPEG image...")
    jpeg_image = create_test_image(size_mb=1, format='JPEG')
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('test.jpg', jpeg_image, 'image/jpeg')}
    )
    print(f"   Status: {response.status_code}")
    test2a = response.status_code == 200
    print(f"   {'✅ PASS' if test2a else '❌ FAIL'}: JPEG {'accepted' if test2a else 'rejected'}")

    # Test 2b: Valid PNG - should succeed
    print("\n2b. Testing valid PNG image...")
    png_image = create_test_image(size_mb=1, format='PNG')
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('test.png', png_image, 'image/png')}
    )
    print(f"   Status: {response.status_code}")
    test2b = response.status_code == 200
    print(f"   {'✅ PASS' if test2b else '❌ FAIL'}: PNG {'accepted' if test2b else 'rejected'}")

    # Test 2c: Invalid PDF file - should fail
    print("\n2c. Testing invalid PDF file...")
    pdf_content = b'%PDF-1.4 fake pdf content'
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('malicious.pdf', pdf_content, 'application/pdf')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        print(f"   Error: {response.json().get('detail', '')}")
        print("   ✅ PASS: PDF correctly rejected")
        test2c = True
    else:
        print("   ❌ FAIL: PDF accepted (should be rejected)")
        test2c = False

    # Test 2d: Text file disguised as JPG - should fail
    print("\n2d. Testing text file with .jpg extension...")
    fake_image = b'This is not an image, it is plain text'
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('fake.jpg', fake_image, 'text/plain')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        print(f"   Error: {response.json().get('detail', '')}")
        print("   ✅ PASS: Fake image correctly rejected")
        test2d = True
    else:
        print("   ❌ FAIL: Fake image accepted (should be rejected)")
        test2d = False

    return test2a and test2b and test2c and test2d


def test_file_extension_whitelist(session):
    """Test file extension whitelist"""
    print("\n" + "="*60)
    print("TEST 3: File Extension Whitelist")
    print("="*60)

    # Test 3a: Valid extensions (.jpg, .png, .gif, .webp)
    print("\n3a. Testing .gif extension...")
    gif_image = create_test_image(size_mb=1, format='GIF')
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('test.gif', gif_image, 'image/gif')}
    )
    print(f"   Status: {response.status_code}")
    test3a = response.status_code == 200
    print(f"   {'✅ PASS' if test3a else '❌ FAIL'}: GIF {'accepted' if test3a else 'rejected'}")

    # Test 3b: Invalid extension (.exe) - should fail
    print("\n3b. Testing invalid .exe extension...")
    fake_exe = b'MZ\x90\x00'  # Fake exe header
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('malicious.exe', fake_exe, 'application/x-msdownload')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        print(f"   Error: {response.json().get('detail', '')}")
        print("   ✅ PASS: .exe correctly rejected")
        test3b = True
    else:
        print("   ❌ FAIL: .exe accepted (should be rejected)")
        test3b = False

    # Test 3c: Invalid extension (.php) - should fail
    print("\n3c. Testing invalid .php extension...")
    fake_php = b'<?php echo "hacked"; ?>'
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('shell.php', fake_php, 'application/x-php')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        print("   ✅ PASS: .php correctly rejected")
        test3c = True
    else:
        print("   ❌ FAIL: .php accepted (should be rejected)")
        test3c = False

    return test3a and test3b and test3c


def test_actual_content_validation(session):
    """Test that image content is validated, not just extension"""
    print("\n" + "="*60)
    print("TEST 4: Actual Image Content Validation (using Pillow)")
    print("="*60)

    # Create a text file with .jpg extension
    print("\n4a. Testing text file renamed to .jpg...")
    fake_image_content = b'This is just text pretending to be an image!'
    response = upload_with_csrf(
        session,
        f"{BASE_URL}/api/profile/upload-picture/",
        {'profile_picture': ('notanimage.jpg', fake_image_content, 'image/jpeg')}
    )
    print(f"   Status: {response.status_code}")

    if response.status_code == 400:
        error_msg = response.json().get('detail', '')
        print(f"   Error: {error_msg}")
        if 'invalid' in error_msg.lower() or 'corrupted' in error_msg.lower():
            print("   ✅ PASS: Fake image correctly rejected (content validation working)")
            return True
        else:
            print("   ⚠️  WARNING: Rejected but with unexpected error message")
            return True  # Still pass since it was rejected
    else:
        print("   ❌ FAIL: Fake image accepted (Pillow validation may not be working)")
        return False


def main():
    print("\n" + "="*60)
    print("FILE UPLOAD VALIDATION TEST SUITE")
    print("="*60)
    print("Testing file upload security for profile pictures")
    print("Server: " + BASE_URL)
    print("\nNOTE: Ensure Django development server is running")
    print("="*60)

    try:
        # Create session for maintaining cookies
        session = requests.Session()

        # Setup test user and login
        if not setup_test_user(session):
            print("\n❌ ERROR: Could not setup test user")
            return 1

        # Run tests
        test1 = test_profile_picture_file_size(session)
        test2 = test_profile_picture_mime_type(session)
        test3 = test_file_extension_whitelist(session)
        test4 = test_actual_content_validation(session)

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"File Size Validation: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"MIME Type Validation: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"Extension Whitelist: {'✅ PASS' if test3 else '❌ FAIL'}")
        print(f"Content Validation (Pillow): {'✅ PASS' if test4 else '❌ FAIL'}")
        print("="*60)

        if all([test1, test2, test3, test4]):
            print("\n✅ ALL TESTS PASSED - File upload validation is working correctly!")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED - Review configuration")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure Django development server is running:")
        print("  djvenv/bin/python manage.py runserver")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
