#!/usr/bin/env python3
"""
SSL Certificate Fix for macOS Python
This script sets up SSL certificates properly for Python on macOS to prevent
"certificate verify failed: unable to get local issuer certificate" errors.
"""

import os
import ssl
import sys
import certifi


def setup_ssl_certificates():
    """Configure SSL certificates for Python on macOS"""
    print("Setting up SSL certificates for Python on macOS...")

    # Get the path to the certifi certificate bundle
    cert_path = certifi.where()
    print(f"Using certificate bundle: {cert_path}")

    # Set environment variables
    os.environ["SSL_CERT_FILE"] = cert_path
    os.environ["REQUESTS_CA_BUNDLE"] = cert_path
    os.environ["CURL_CA_BUNDLE"] = cert_path

    # Create default SSL context with proper certificates
    ssl_context = ssl.create_default_context(cafile=cert_path)
    ssl._create_default_https_context = lambda: ssl_context

    print("✅ SSL certificates configured successfully!")
    print("Environment variables set:")
    print(f"  SSL_CERT_FILE={cert_path}")
    print(f"  REQUESTS_CA_BUNDLE={cert_path}")
    print(f"  CURL_CA_BUNDLE={cert_path}")

    return cert_path


def add_to_shell_profile():
    """Add SSL certificate setup to shell profile"""
    cert_path = certifi.where()

    # Shell commands to add to profile
    shell_commands = f"""
# SSL Certificate fix for Python on macOS
export SSL_CERT_FILE="{cert_path}"
export REQUESTS_CA_BUNDLE="{cert_path}"
export CURL_CA_BUNDLE="{cert_path}"
"""

    # Detect shell and add to appropriate profile
    shell = os.environ.get("SHELL", "/bin/zsh")

    if "zsh" in shell:
        profile_file = os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
        profile_file = os.path.expanduser("~/.bash_profile")
    else:
        profile_file = os.path.expanduser("~/.profile")

    print(f"\nAdding SSL certificate configuration to {profile_file}")

    # Check if already configured
    try:
        with open(profile_file, "r") as f:
            content = f.read()
            if "SSL_CERT_FILE" in content and cert_path in content:
                print(
                    "✅ SSL certificate configuration already exists in shell profile"
                )
                return
    except FileNotFoundError:
        pass

    # Add configuration
    with open(profile_file, "a") as f:
        f.write(shell_commands)

    print(f"✅ Added SSL certificate configuration to {profile_file}")
    print(
        "Please run 'source ~/.zshrc' or restart your terminal for changes to take effect"
    )


def test_ssl_connection():
    """Test SSL connection to verify the fix works"""
    import urllib.request

    print("\nTesting SSL connection...")
    try:
        response = urllib.request.urlopen("https://pypi.org/simple/")
        print("✅ SSL connection test successful!")
        return True
    except Exception as e:
        print(f"❌ SSL connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("macOS Python SSL Certificate Fix")
    print("=" * 40)

    # Setup SSL certificates
    setup_ssl_certificates()

    # Add to shell profile for permanent fix
    add_to_shell_profile()

    # Test the connection
    test_ssl_connection()

    print("\n" + "=" * 40)
    print("Setup complete! Your Python SSL certificates should now work properly.")
    print("If you continue to have issues, try restarting your terminal or running:")
    print("  source ~/.zshrc")
