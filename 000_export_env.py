import os
from dotenv import load_dotenv
import sys

def export_env_variables():
    """
    Load all environment variables from .env file and export them
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
            
        # Export all variables to environment
        for key, value in env_vars.items():
            os.environ[key] = value
        
        print("✅ Environment variables exported successfully:")
        for key, value in env_vars.items():
            # Mask sensitive values (API keys, tokens, etc.)
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password']):
                masked_value = '*' * len(value) if value else 'Not set'
                print(f"{key}: {masked_value}")
            else:
                print(f"{key}: {value}")
        
    except FileNotFoundError:
        print("❌ .env file not found")
        print("Please create a .env file with your environment variables")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading environment variables: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    export_env_variables()
