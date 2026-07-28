from app.utils.chunk_calculator import chunk_calculator

# Test dynamic chunk size calculation with different record counts
test_cases = [
    (0, "Empty dataset"),
    (100, "Small dataset"),
    (1000, "Medium dataset"),
    (10000, "Large dataset"),
    (100000, "Very large dataset"),
    (1000000, "Massive dataset"),
    (5000000, "Enterprise dataset")
]

print("Dynamic Chunk Size Calculator Test Results:")
print("=" * 60)

for record_count, description in test_cases:
    chunk_size = chunk_calculator.calculate_chunk_size(record_count)
    estimated_chunks = chunk_calculator.estimate_chunks(record_count, chunk_size)
    
    print(f"\n{description}:")
    print(f"  Records: {record_count:,}")
    print(f"  Chunk Size: {chunk_size:,}")
    print(f"  Estimated Chunks: {estimated_chunks:,}")
    print(f"  Progress per Chunk: {chunk_calculator.get_progress_percentage(1, estimated_chunks):.2f}%")

print("\n" + "=" * 60)
print("Test completed successfully!")
