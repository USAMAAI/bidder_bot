#!/usr/bin/env python3
"""
Launcher script for the Upwork AI Jobs Applier Streamlit app.
Checks dependencies and starts the application.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    required_packages = ['streamlit', 'pandas', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check if environment is properly configured."""
    issues = []
    
    # Check if profile file exists
    profile_path = Path("./files/profile.md")
    if not profile_path.exists():
        issues.append("Profile file not found: ./files/profile.md")
    
    # Check API key (optional - can be set in app)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not set in environment (can be set in app)")
    else:
        print("✅ OpenAI API key is set")
    
    if issues:
        print("❌ Environment issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Environment is properly configured")
    return True

def start_streamlit():
    """Start the Streamlit application."""
    print("🚀 Starting Upwork AI Jobs Applier...")
    print("📱 The app will open in your browser at: http://localhost:8501")
    print("🔄 Use Ctrl+C to stop the application")
    print("-" * 60)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
    except FileNotFoundError:
        print("❌ Streamlit not found. Install it with: pip install streamlit")

def main():
    """Main launcher function."""
    print("🤖 Upwork AI Jobs Applier - Launcher")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment (warnings only)
    check_environment()
    
    print("\n" + "=" * 50)
    
    # Start the application
    start_streamlit()

if __name__ == "__main__":
    main() 