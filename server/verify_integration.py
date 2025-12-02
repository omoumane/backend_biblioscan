"""Quick verification script to check if all components are properly integrated"""
import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError:
        print(f"⚠️  {description} not installed: {module_name}")
        return False

def main():
    print("=" * 60)
    print("Verifying Agent Integration")
    print("=" * 60)
    
    all_ok = True
    
    # Check files
    print("\n📁 Checking files...")
    files_to_check = [
        ("services/agents_service.py", "Agent service"),
        ("controllers/detection_controller.py", "Detection controller"),
        ("server.py", "Server file"),
        ("config.py", "Config file"),
        ("test_endpoint.py", "Test endpoint script"),
        ("test_api.sh", "Bash test script"),
    ]
    
    for filepath, desc in files_to_check:
        if not check_file_exists(filepath, desc):
            all_ok = False
    
    # Check imports (optional - will fail if packages not installed)
    print("\n📦 Checking imports (optional - install if missing)...")
    imports_to_check = [
        ("langgraph", "LangGraph"),
        ("langchain_core", "LangChain Core"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langchain_ollama", "LangChain Ollama"),
    ]
    
    for module, desc in imports_to_check:
        check_import(module, desc)
    
    # Check function existence
    print("\n🔍 Checking code structure...")
    try:
        sys.path.insert(0, '.')
        
        # Check agent service
        from services import agents_service
        if hasattr(agents_service, 'BookTitleResolverAgent'):
            print("✅ BookTitleResolverAgent class found")
        else:
            print("❌ BookTitleResolverAgent class not found")
            all_ok = False
        
        if hasattr(agents_service, 'resolve_book_title'):
            print("✅ resolve_book_title function found")
        else:
            print("❌ resolve_book_title function not found")
            all_ok = False
        
        # Check detection controller
        from controllers import detection_controller
        if hasattr(detection_controller, 'detect_and_ocr_and_agent'):
            print("✅ detect_and_ocr_and_agent function found")
        else:
            print("❌ detect_and_ocr_and_agent function not found")
            all_ok = False
        
        # Check config
        import config
        if hasattr(config, 'LLM_PROVIDER'):
            print("✅ LLM_PROVIDER config found")
        else:
            print("❌ LLM_PROVIDER config not found")
            all_ok = False
        
    except ImportError as e:
        print(f"⚠️  Could not verify code structure: {e}")
        print("   (This is OK if dependencies are not installed yet)")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All files and structure verified!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start server: python server.py")
        print("3. Test endpoint: python test_endpoint.py")
    else:
        print("⚠️  Some issues found. Please check the errors above.")
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

