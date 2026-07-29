"""
Test the Generation Monitor System
"""
from generation_monitor import GenerationMonitor
import time

# Create monitor instance
monitor = GenerationMonitor()
monitor.start()

# Simulate some batch operations
print("Simulating batch operations...")

for i in range(5):
    time.sleep(0.1)  # Simulate batch processing
    monitor.record_batch('test_table', 1000, 0.1)
    print(f"  Batch {i+1} recorded")

# Simulate a deadlock
monitor.record_deadlock('test_table')
print("  Deadlock recorded")

# Simulate read-only wait
monitor.record_readonly(5.0)
print("  Read-only event recorded (5s wait)")

# Simulate a resume
monitor.record_resume()
print("  Resume event recorded")

# Stop monitoring
monitor.stop()

# Get summary
summary = monitor.get_summary()

print("\n" + "=" * 80)
print("MONITORING SUMMARY")
print("=" * 80)
print(f"Total batches: {summary['batch_metrics']['total_batches']}")
print(f"Total rows inserted: {summary['batch_metrics']['total_rows_inserted']:,}")
print(f"Average batch time: {summary['batch_metrics']['average_batch_time_seconds']:.4f}s")
print(f"Average throughput: {summary['batch_metrics']['average_rows_per_second']:.2f} rows/sec")
print(f"Peak throughput: {summary['batch_metrics']['peak_throughput_rows_per_second']:.2f} rows/sec")
print(f"Deadlocks encountered: {summary['error_handling']['deadlock_count']}")
print(f"Read-only events: {summary['error_handling']['readonly_event_count']}")
print(f"Total read-only wait time: {summary['error_handling']['total_readonly_wait_time_formatted']}")
print(f"Resume count: {summary['resilience']['resume_count']}")

# Export JSON
json_file = monitor.export_json("test_monitor_report.json")
print(f"\n✓ JSON report exported: {json_file}")

# Export PDF
pdf_file = monitor.export_pdf("test_monitor_report.pdf")
print(f"✓ PDF report exported: {pdf_file}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
