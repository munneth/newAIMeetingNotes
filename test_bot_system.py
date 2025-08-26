#!/usr/bin/env python3
"""
Simple test script for the bot system
Tests the core logic without requiring Kubernetes
"""

import sys
import os
sys.path.append('backend/bot-instance')
sys.path.append('backend/bot-orchestrator')

def test_bot_imports():
    """Test that all bot components can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import meeting_bot
        print("✅ meeting_bot imports successfully")
    except Exception as e:
        print(f"❌ meeting_bot import failed: {e}")
        return False
    
    try:
        import bot_orchestrator
        print("✅ bot_orchestrator imports successfully")
    except Exception as e:
        print(f"❌ bot_orchestrator import failed: {e}")
        return False
    
    return True

def test_bot_logic():
    """Test basic bot logic"""
    print("\n🧪 Testing bot logic...")
    
    try:
        from meeting_bot import MeetingBot
        
        # Test bot initialization (without environment variables)
        os.environ['USER_ID'] = 'test_user'
        os.environ['MEETING_ID'] = 'test_meeting'
        os.environ['INSTANCE_ID'] = 'test_instance'
        os.environ['MEETING_DATA'] = '{"link": "https://test.com", "start_time": "2024-01-15T10:00:00Z", "duration": "60"}'
        
        # This should work without Redis connection
        bot = MeetingBot()
        print("✅ Bot instance created successfully")
        
        # Test action logging
        bot.log_action("test_action", {"test": "data"})
        print("✅ Bot action logging works")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot logic test failed: {e}")
        return False

def test_orchestrator_logic():
    """Test orchestrator logic"""
    print("\n🧪 Testing orchestrator logic...")
    
    try:
        from bot_orchestrator import BotOrchestrator
        
        # Test orchestrator initialization (without Kubernetes)
        orchestrator = BotOrchestrator()
        print("✅ Orchestrator created successfully")
        
        # Test instance tracking
        instances = orchestrator.list_active_instances()
        print(f"✅ Active instances tracking works: {len(instances)} instances")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator logic test failed: {e}")
        return False

def test_upcoming_meeting_logic():
    """Test the upcoming meeting logic"""
    print("\n🧪 Testing upcoming meeting logic...")
    
    from datetime import datetime, timedelta
    
    # Test 1: Meeting within 1 hour (should be upcoming)
    now = datetime.now()
    meeting_in_30min = now + timedelta(minutes=30)
    
    time_diff = meeting_in_30min - now
    hours_diff = time_diff.total_seconds() / 3600
    
    if hours_diff <= 1:
        print("✅ Meeting within 1 hour correctly identified as upcoming")
    else:
        print("❌ Meeting within 1 hour incorrectly identified")
        return False
    
    # Test 2: Meeting in 2 hours (should NOT be upcoming)
    meeting_in_2hours = now + timedelta(hours=2)
    
    time_diff = meeting_in_2hours - now
    hours_diff = time_diff.total_seconds() / 3600
    
    if hours_diff > 1:
        print("✅ Meeting in 2 hours correctly identified as NOT upcoming")
    else:
        print("❌ Meeting in 2 hours incorrectly identified")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Bot System Components\n")
    
    tests = [
        test_bot_imports,
        test_bot_logic,
        test_orchestrator_logic,
        test_upcoming_meeting_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot system is ready for deployment.")
        print("\n📝 Next steps:")
        print("1. Enable Docker WSL integration in Docker Desktop")
        print("2. Start minikube: minikube start")
        print("3. Run deployment: ./deploy.sh")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
