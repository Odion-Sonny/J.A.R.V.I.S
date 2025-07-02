#!/usr/bin/env python3
"""
JARVIS AI Assistant Startup Script
Starts the Python backend and then launches the Electron frontend
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

class JarvisLauncher:
    def __init__(self):
        self.python_process = None
        self.electron_process = None
        self.base_dir = Path(__file__).parent
        self.python_backend_dir = self.base_dir / "python-backend"
        self.electron_app_dir = self.base_dir / "electron-app"
    
    def check_dependencies(self):
        """Check if all dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import gpt4all
            import fastapi
            import uvicorn
            print("✅ Python dependencies are installed")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Installing Python dependencies...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                str(self.python_backend_dir / "requirements.txt")
            ], check=True)
        
        # Check Node.js dependencies
        if not (self.electron_app_dir / "node_modules").exists():
            print("📦 Installing Node.js dependencies...")
            subprocess.run([
                "npm", "install"
            ], cwd=self.electron_app_dir, check=True)
        else:
            print("✅ Node.js dependencies are installed")
    
    def start_python_backend(self):
        """Start the Python backend server"""
        print("🐍 Starting Python backend...")
        
        try:
            self.python_process = subprocess.Popen([
                sys.executable, "ipc_server.py",
                "--host", "127.0.0.1",
                "--port", "8000"
            ], cwd=self.python_backend_dir, 
               stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE)
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            if self.python_process.poll() is None:
                print("✅ Python backend started successfully on port 8000")
                return True
            else:
                stdout, stderr = self.python_process.communicate()
                print(f"❌ Python backend failed to start:")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Python backend: {e}")
            return False
    
    def start_electron_frontend(self):
        """Start the Electron frontend"""
        print("⚡ Starting Electron frontend...")
        
        try:
            self.electron_process = subprocess.Popen([
                "npm", "start"
            ], cwd=self.electron_app_dir)
            
            print("✅ Electron frontend started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Electron frontend: {e}")
            return False
    
    def cleanup(self, signum=None, frame=None):
        """Clean up processes on exit"""
        print("\n🧹 Cleaning up...")
        
        if self.electron_process:
            print("Stopping Electron frontend...")
            self.electron_process.terminate()
            try:
                self.electron_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.electron_process.kill()
        
        if self.python_process:
            print("Stopping Python backend...")
            self.python_process.terminate()
            try:
                self.python_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.python_process.kill()
        
        print("✅ Cleanup complete")
    
    def run(self):
        """Main run method"""
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        try:
            print("🤖 JARVIS AI Assistant")
            print("=" * 50)
            
            # Check dependencies
            self.check_dependencies()
            
            # Start backend
            if not self.start_python_backend():
                print("❌ Failed to start Python backend")
                return 1
            
            # Start frontend
            if not self.start_electron_frontend():
                print("❌ Failed to start Electron frontend")
                self.cleanup()
                return 1
            
            print("\n🎉 JARVIS is now running!")
            print("📝 Backend API: http://127.0.0.1:8000")
            print("🖥️  Frontend: Electron window should open")
            print("🛑 Press Ctrl+C to stop JARVIS")
            
            # Wait for Electron process to finish
            try:
                self.electron_process.wait()
            except KeyboardInterrupt:
                pass
            
            self.cleanup()
            return 0
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.cleanup()
            return 1

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant - Local AI with futuristic interface")
    parser.add_argument("--help-full", action="store_true", 
                       help="Show detailed usage information")
    
    args, unknown = parser.parse_known_args()
    
    if args.help_full:
        print("""
🤖 JARVIS AI Assistant - Help

QUICK START:
    python3 start_jarvis.py

FEATURES:
    🧠 Local AI with GPT4All (privacy-focused)
    📁 File management (create, search, read files)
    ⏰ Alarms and reminders
    🖥️  System monitoring and app launching
    🎤 Voice input and text-to-speech
    🎨 Futuristic UI with multiple themes

COMMANDS YOU CAN TRY:
    "Create a document called meeting-notes.txt"
    "Find all PDF files in my documents"
    "Set a reminder for 30 minutes to check the oven"
    "Show me the current system information"
    "Open calculator"

REQUIREMENTS:
    - Python 3.9+ with pip
    - Node.js 16+ with npm
    - 4GB RAM (8GB recommended)
    - 2GB free disk space

TROUBLESHOOTING:
    - Backend issues: Check Python dependencies
    - Frontend issues: Check Node.js dependencies  
    - Voice issues: Check microphone permissions
    - Performance: Ensure 8GB+ RAM for optimal AI

For full documentation, see README.md
        """)
        return 0
    
    launcher = JarvisLauncher()
    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())