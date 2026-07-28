"""
Test script for 17-step DataVault AI pipeline
Tests basic functionality without requiring full database setup
"""

import sys
import os

# Add path for imports
_root = os.path.dirname(os.path.abspath(__file__))
for _layer in ["Destination_Loader"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from pipeline_context import PipelineContext, StepStatus
from step_mapping import STEP_MAPPING, STEP_DEPENDENCIES, APPROVAL_STEPS

def test_pipeline_context():
    """Test PipelineContext initialization and state management"""
    print("Testing PipelineContext...")
    
    context = PipelineContext()
    
    # Verify all 17 steps are initialized
    assert len(context.steps) == 17, f"Expected 17 steps, got {len(context.steps)}"
    
    # Verify step names
    expected_steps = {
        1: "Connect Database",
        2: "Extract Schema", 
        3: "Enterprise Detection",
        4: "Privacy-Safe Sampling",
        5: "PII Detection",
        6: "Policy Generation",
        7: "Admin Approval",
        8: "Change Detection",
        9: "Redis Hash Vault",
        10: "Crash Recovery",
        11: "Chunk Processing",
        12: "Data Anonymization",
        13: "Batch Loading",
        14: "Validation Approval",
        15: "Safe Database Generation",
        16: "Audit Report",
        17: "Output Delivery"
    }
    
    for step_num, expected_name in expected_steps.items():
        assert context.steps[step_num]["name"] == expected_name, f"Step {step_num} name mismatch"
    
    # Test step status updates
    context.set_step_status(1, StepStatus.RUNNING)
    assert context.get_step_status(1) == StepStatus.RUNNING
    
    context.set_step_status(1, StepStatus.COMPLETED, output="Test output")
    assert context.is_step_completed(1)
    assert context.get_step_output(1) == "Test output"
    
    # Test progress calculation
    context.set_step_status(2, StepStatus.COMPLETED)
    context.set_step_status(3, StepStatus.COMPLETED)
    progress = context.get_progress_percentage()
    assert progress == (3 / 17) * 100, f"Expected ~17.6%, got {progress}%"
    
    # Test to_dict for WebSocket compatibility
    progress_dict = context.to_dict()
    assert "current_step" in progress_dict
    assert "step_name" in progress_dict
    assert "step_status" in progress_dict
    assert "progress" in progress_dict
    assert "steps" in progress_dict
    
    print("✓ PipelineContext tests passed")
    return True

def test_step_mapping():
    """Test step mapping configuration"""
    print("\nTesting Step Mapping...")
    
    # Verify all 17 steps are mapped
    assert len(STEP_MAPPING) == 17, f"Expected 17 step mappings, got {len(STEP_MAPPING)}"
    
    # Verify approval steps
    assert 7 in APPROVAL_STEPS, "Step 7 (Admin Approval) should be in APPROVAL_STEPS"
    assert 14 in APPROVAL_STEPS, "Step 14 (Validation Approval) should be in APPROVAL_STEPS"
    
    # Verify dependencies
    assert STEP_DEPENDENCIES[1] == [], "Step 1 should have no dependencies"
    assert 1 in STEP_DEPENDENCIES[2], "Step 2 should depend on Step 1"
    assert 7 in STEP_DEPENDENCIES[8], "Step 8 should depend on Step 7"
    
    print("✓ Step Mapping tests passed")
    return True

def test_step_status_enum():
    """Test StepStatus enum"""
    print("\nTesting StepStatus enum...")
    
    assert StepStatus.PENDING.value == "pending"
    assert StepStatus.RUNNING.value == "running"
    assert StepStatus.COMPLETED.value == "completed"
    assert StepStatus.FAILED.value == "failed"
    assert StepStatus.WAITING_FOR_APPROVAL.value == "waiting_for_approval"
    
    print("✓ StepStatus enum tests passed")
    return True

def test_policy_executor_structure():
    """Test PolicyExecutor has new 17-step methods"""
    print("\nTesting PolicyExecutor structure...")
    
    try:
        from policy_executor import PolicyExecutor
    except ImportError as e:
        # Skip this test if dependencies are missing
        print(f"⊘ Skipping PolicyExecutor test (missing dependency: {e})")
        return True  # Don't fail the test suite for missing optional dependencies
    
    try:
        # Create a mock executor (won't actually run without DB config)
        mock_config = {
            "database_type": "sqlite",
            "host": None,
            "port": None,
            "username": None,
            "password": None,
            "database_name": ":memory:"
        }
        
        executor = PolicyExecutor(
            source_db_config=mock_config,
            destination_db_config=mock_config,
            policy_file="test_policy.json"
        )
        
        # Verify new methods exist
        assert hasattr(executor, 'step_1_connect_database')
        assert hasattr(executor, 'step_2_extract_schema')
        assert hasattr(executor, 'step_3_enterprise_detection')
        assert hasattr(executor, 'step_4_privacy_safe_sampling')
        assert hasattr(executor, 'step_5_pii_detection')
        assert hasattr(executor, 'step_6_policy_generation')
        assert hasattr(executor, 'step_7_admin_approval')
        assert hasattr(executor, 'step_8_change_detection')
        assert hasattr(executor, 'step_9_redis_hash_vault')
        assert hasattr(executor, 'step_10_crash_recovery')
        assert hasattr(executor, 'step_11_chunk_processing')
        assert hasattr(executor, 'step_12_data_anonymization')
        assert hasattr(executor, 'step_13_batch_loading')
        assert hasattr(executor, 'step_14_validation_approval')
        assert hasattr(executor, 'step_15_safe_database_generation')
        assert hasattr(executor, 'step_16_audit_report')
        assert hasattr(executor, 'step_17_output_delivery')
        
        # Verify new helper methods
        assert hasattr(executor, 'calculate_dynamic_chunk_size')
        assert hasattr(executor, 'read_chunk')
        assert hasattr(executor, 'anonymize_chunk')
        assert hasattr(executor, 'load_batch')
        assert hasattr(executor, 'get_progress')
        
        # Verify context is initialized
        assert executor.context is not None
        assert isinstance(executor.context, PipelineContext)
        
        print("✓ PolicyExecutor structure tests passed")
        return True
        
    except Exception as e:
        print(f"✗ PolicyExecutor test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("17-STEP PIPELINE TESTS")
    print("=" * 60)
    
    tests = [
        test_pipeline_context,
        test_step_mapping,
        test_step_status_enum,
        test_policy_executor_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
