"""
Performance Analysis for CRM Dataset Generation
"""
import os
import time
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Get MySQL connection with SSL"""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USERNAME'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        ssl={'ssl_mode': 'PREFERRED'}
    )

def measure_network_latency(connection):
    """Measure network latency to Aiven"""
    cursor = connection.cursor()
    
    latencies = []
    for i in range(10):
        start = time.time()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        end = time.time()
        latencies.append((end - start) * 1000)  # Convert to ms
    
    cursor.close()
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    return avg_latency, min_latency, max_latency

def get_storage_stats(connection):
    """Get storage statistics"""
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT table_name, table_rows, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
               ROUND((data_length / 1024 / 1024), 2) AS data_mb,
               ROUND((index_length / 1024 / 1024), 2) AS index_mb
        FROM information_schema.TABLES
        WHERE table_schema = %s
        ORDER BY (data_length + index_length) DESC
    """, (os.getenv('MYSQL_DATABASE'),))
    
    stats = cursor.fetchall()
    cursor.close()
    
    total_mb = sum(row[2] for row in stats)
    total_rows = sum(row[1] for row in stats)
    total_data_mb = sum(row[3] for row in stats)
    total_index_mb = sum(row[4] for row in stats)
    
    return stats, total_rows, total_mb, total_data_mb, total_index_mb

def measure_insert_performance(connection):
    """Measure INSERT performance with different batch sizes"""
    cursor = connection.cursor()
    
    # Create a test table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_test (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing data
    cursor.execute("TRUNCATE TABLE performance_test")
    connection.commit()
    
    results = {}
    
    for batch_size in [100, 500, 1000, 2500, 5000, 10000]:
        print(f"\nTesting batch size: {batch_size}")
        
        # Generate test data
        test_data = [(f"test_data_{i}",) for i in range(batch_size)]
        
        # Measure insertion time
        start = time.time()
        cursor.executemany("INSERT INTO performance_test (data) VALUES (%s)", test_data)
        connection.commit()
        end = time.time()
        
        elapsed = end - start
        rows_per_sec = batch_size / elapsed
        
        results[batch_size] = {
            'elapsed_seconds': elapsed,
            'rows_per_second': rows_per_sec,
            'time_per_row_ms': (elapsed / batch_size) * 1000
        }
        
        print(f"  Elapsed: {elapsed:.4f}s")
        print(f"  Rows/sec: {rows_per_sec:.2f}")
        print(f"  Time/row: {(elapsed / batch_size) * 1000:.4f}ms")
        
        # Clear for next test
        cursor.execute("TRUNCATE TABLE performance_test")
        connection.commit()
    
    # Drop test table
    cursor.execute("DROP TABLE performance_test")
    connection.commit()
    
    cursor.close()
    return results

def analyze_current_progress():
    """Analyze current generation progress"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current counts
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return counts

print("=" * 80)
print("PERFORMANCE ANALYSIS FOR CRM DATASET GENERATION")
print("=" * 80)

# 1. Network Latency
print("\n1. NETWORK LATENCY TO AIVEN")
print("-" * 80)
conn = get_connection()
avg_latency, min_latency, max_latency = measure_network_latency(conn)
print(f"Average latency: {avg_latency:.2f} ms")
print(f"Min latency: {min_latency:.2f} ms")
print(f"Max latency: {max_latency:.2f} ms")

# 2. Storage Statistics
print("\n2. CURRENT STORAGE STATISTICS")
print("-" * 80)
stats, total_rows, total_mb, total_data_mb, total_index_mb = get_storage_stats(conn)
print(f"Total rows: {total_rows:,}")
print(f"Total size: {total_mb:.2f} MB ({total_mb/1024:.2f} GB)")
print(f"Data size: {total_data_mb:.2f} MB ({total_data_mb/1024:.2f} GB)")
print(f"Index size: {total_index_mb:.2f} MB ({total_index_mb/1024:.2f} GB)")
print(f"Index ratio: {(total_index_mb/total_data_mb)*100:.1f}%")

print("\nTable breakdown (by size):")
for table, rows, size_mb, data_mb, index_mb in stats[:10]:
    print(f"  {table:25s} {rows:>10,} rows  {size_mb:>8.2f} MB (data: {data_mb:.2f}MB, index: {index_mb:.2f}MB)")

# 3. INSERT Performance Test
print("\n3. INSERT PERFORMANCE TEST (different batch sizes)")
print("-" * 80)
insert_results = measure_insert_performance(conn)

# 4. Current Progress Analysis
print("\n4. CURRENT GENERATION PROGRESS")
print("-" * 80)
current_counts = analyze_current_progress()

target_sizes = {
    'companies': 24500,
    'customers': 495000,
    'contacts': 740000,
    'sales_representatives': 4750,
    'leads': 300000,
    'opportunities': 250000,
    'contracts': 150000,
    'support_tickets': 1000000,
    'activities': 2000000,
    'invoices': 500000
}

total_current = sum(current_counts.values())
total_target = sum(target_sizes.values())

print(f"Total current: {total_current:,} rows")
print(f"Total target: {total_target:,} rows")
print(f"Progress: {(total_current/total_target)*100:.1f}%")

# 5. Calculate estimated final size
print("\n5. ESTIMATED FINAL DATABASE SIZE")
print("-" * 80)
avg_bytes_per_row = (total_mb * 1024 * 1024) / total_current if total_current > 0 else 0
estimated_final_mb = (total_target * avg_bytes_per_row) / (1024 * 1024)
estimated_final_gb = estimated_final_mb / 1024

print(f"Average bytes per row: {avg_bytes_per_row:.2f}")
print(f"Estimated final size: {estimated_final_mb:.2f} MB ({estimated_final_gb:.2f} GB)")

# 6. Performance Analysis Summary
print("\n6. PERFORMANCE ANALYSIS SUMMARY")
print("-" * 80)

# Calculate current insertion rate from the script output
# Based on the ETA progression: 260,000 rows in ~4 minutes = ~1,083 rows/sec
# But the ETA is increasing, suggesting slowing performance
current_rows_per_sec = 10000 / 7.2  # Approximate from script output (10K in ~7.2s based on ETA trend)
print(f"Current insertion rate: ~{current_rows_per_sec:.1f} rows/sec")
print(f"Current batch size: 10,000 rows")
print(f"Time per batch: ~7.2 seconds")

# Find optimal batch size from test
optimal_batch_size = max(insert_results.keys(), key=lambda x: insert_results[x]['rows_per_second'])
optimal_rate = insert_results[optimal_batch_size]['rows_per_second']
print(f"\nOptimal batch size from test: {optimal_batch_size}")
print(f"Optimal insertion rate: {optimal_rate:.1f} rows/sec")

# 7. Bottleneck Analysis
print("\n7. BOTTLENECK ANALYSIS")
print("-" * 80)
print("Factors to consider:")
print(f"  - Network latency: {avg_latency:.2f}ms (acceptable)")
print(f"  - Index ratio: {(total_index_mb/total_data_mb)*100:.1f}% (indexes are significant)")
print(f"  - Current rate: {current_rows_per_sec:.1f} rows/sec vs optimal: {optimal_rate:.1f} rows/sec")
print(f"  - Performance gap: {(1 - current_rows_per_sec/optimal_rate)*100:.1f}%")

if current_rows_per_sec < optimal_rate * 0.5:
    print("\n  LIKELY BOTTLENECK: Faker data generation or SSL overhead")
elif (total_index_mb/total_data_mb) > 0.5:
    print("\n  LIKELY BOTTLENECK: Index maintenance during INSERT")
else:
    print("\n  LIKELY BOTTLENECK: Network or MySQL commit time")

# 8. Recommendations
print("\n8. RECOMMENDATIONS")
print("-" * 80)
print(f"Optimal batch size for Aiven Free plan: {optimal_batch_size}")
print(f"Estimated final database size: {estimated_final_gb:.2f} GB")

# Aiven Free plan typically has 10GB storage
aiven_free_storage_gb = 10
remaining_storage = aiven_free_storage_gb - estimated_final_gb
print(f"Aiven Free plan storage: {aiven_free_storage_gb} GB")
print(f"Estimated remaining storage: {remaining_storage:.2f} GB")

if remaining_storage < 0:
    print("  ⚠ WARNING: Estimated size exceeds Aiven Free plan storage!")
    print("  Recommendation: Reduce target sizes or upgrade plan")
elif remaining_storage < 2:
    print("  ⚠ WARNING: Approaching storage limit!")
    print("  Recommendation: Monitor closely, consider cleanup or upgrade")
else:
    print("  ✓ Storage should be sufficient")

print("\nPerformance recommendations:")
print(f"  - Use batch size of {optimal_batch_size} for optimal throughput")
print("  - Consider disabling indexes during bulk load, then rebuild")
print("  - Consider increasing chunk size to reduce commit frequency")
print("  - Monitor for read-only states and adjust retry logic accordingly")

conn.close()

print("\n" + "=" * 80)
print("PERFORMANCE ANALYSIS COMPLETE")
print("=" * 80)
