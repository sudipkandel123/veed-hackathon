import os
from dotenv import load_dotenv
import sys
import subprocess

def export_env_variables():
    """
    Load environment variables from .env file and export them to the terminal session
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get all environment variables that were loaded from .env
        env_vars = {key: value for key, value in os.environ.items() 
                   if key in os.environ and key not in os.environ._data}
        
        if not env_vars:
            print("⚠️ No environment variables found in .env file")
            return
            
        # Export variables to terminal session
        for key, value in env_vars.items():
            # For Unix-like systems (macOS, Linux)
            if os.name != 'nt':  # not Windows
                export_cmd = f'export {key}="{value}"'
                subprocess.run(['echo', export_cmd], shell=True)
                os.environ[key] = value
            # For Windows
            else:
                set_cmd = f'set {key}={value}'
                subprocess.run(['echo', set_cmd], shell=True)
                os.environ[key] = value
        
        print("\n✅ Environment variables exported successfully to terminal session:")
        for key, value in env_vars.items():
            # Mask sensitive values (API keys, tokens, etc.)
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password']):
                masked_value = '*' * len(value) if value else 'Not set'
                print(f"{key}: {masked_value}")
            else:
                print(f"{key}: {value}")
        
        print("\n📝 To use these variables in your current terminal session, run:")
        if os.name != 'nt':  # not Windows
            print("source <(python env_loader.py)")
        else:
            print("python env_loader.py")
        
    except FileNotFoundError:
        print("❌ .env file not found")
        print("Please create a .env file with your environment variables")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading environment variables: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    export_env_variables() 