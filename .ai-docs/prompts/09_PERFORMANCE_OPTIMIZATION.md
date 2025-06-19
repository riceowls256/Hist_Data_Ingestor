# Performance Optimization Prompt

## Context
Use this when performance issues are identified and optimization is needed.

## Prompt

We need to optimize the performance of [COMPONENT/FEATURE]. Current performance is [CURRENT_METRICS] and we need to achieve [TARGET_METRICS].

### Performance Requirements

**Optimization Goals**:
- [ ] Response time: Current [X]ms → Target [Y]ms
- [ ] Throughput: Current [X]rps → Target [Y]rps  
- [ ] Memory usage: Current [X]GB → Target [Y]GB
- [ ] CPU usage: Current [X]% → Target [Y]%

**Constraints**:
- [ ] Maintain backward compatibility
- [ ] No breaking API changes
- [ ] Budget: [time/resource constraints]
- [ ] Must work with existing infrastructure

### Performance Analysis Process

1. **Baseline Measurement**
   
   First, establish accurate baseline:
   ```bash
   # CPU profiling
   python -m cProfile -o baseline.prof src/main.py
   
   # Memory profiling
   python -m memory_profiler src/main.py
   
   # Load testing
   locust -f tests/load_test.py --headless -u 1000 -r 100 -t 300s
   
   # Database query analysis
   python analyze_slow_queries.py
   ```

2. **Identify Bottlenecks**
   
   Document findings:
   ```markdown
   ## Bottleneck Analysis
   
   ### Finding 1: [Bottleneck name]
   - Location: [file:line]
   - Impact: [X]ms per request
   - Frequency: [X] times per request
   - Total impact: [X]% of response time
   
   ### Finding 2: [Bottleneck name]
   [repeat structure]
   ```

3. **Create Optimization Plan**
   
   For each bottleneck:
   ```markdown
   ## Optimization: [Name]
   
   ### Current Implementation
   [code snippet or description]
   
   ### Proposed Optimization
   [new approach]
   
   ### Expected Improvement
   - Performance gain: [X]%
   - Implementation effort: [hours]
   - Risk level: LOW|MEDIUM|HIGH
   - Rollback plan: [how to revert]
   ```

4. **Implement Optimizations**
   
   For each optimization:
   - Create feature branch
   - Implement change
   - Add performance test
   - Measure improvement
   - Document results

5. **Verification Testing**
   
   After each optimization:
   ```bash
   # Re-run performance tests
   python performance_test.py --compare baseline.json
   
   # Verify functionality
   pytest tests/ -v
   
   # Check for memory leaks
   python memory_leak_test.py --duration 3600
   ```

### Optimization Techniques Checklist

Consider these approaches:

#### Code Level
- [ ] Algorithm optimization (O(n²) → O(n log n))
- [ ] Remove unnecessary loops
- [ ] Lazy loading/evaluation
- [ ] Parallel processing
- [ ] Batch operations

#### Database Level
- [ ] Add missing indexes
- [ ] Optimize queries
- [ ] Implement query caching
- [ ] Database connection pooling
- [ ] Denormalization where appropriate

#### Caching
- [ ] Add Redis/Memcached
- [ ] Implement application-level caching
- [ ] Cache warming strategies
- [ ] CDN for static assets

#### Infrastructure
- [ ] Horizontal scaling
- [ ] Load balancing optimization
- [ ] Resource limits tuning
- [ ] Network optimization

### Performance Testing Script

Create automated performance test:

```python
# performance_test_suite.py
def test_response_time():
    # Test p95 response time
    pass

def test_throughput():
    # Test requests per second
    pass

def test_memory_usage():
    # Test memory consumption
    pass

def test_concurrent_users():
    # Test with increasing load
    pass
```

### Results Documentation

Update documentation with:

```markdown
# Performance Optimization Results

## Summary
- Overall improvement: [X]%
- Target metrics achieved: [Y/N]
- Trade-offs made: [list]

## Detailed Results
| Metric | Before | After | Target | Achieved |
|--------|--------|-------|--------|----------|
| Response Time (p95) | Xms | Yms | Zms | ✅/❌ |
| Throughput | Xrps | Yrps | Zrps | ✅/❌ |

## Optimizations Applied
1. [Optimization 1]: [Impact]
2. [Optimization 2]: [Impact]

## Lessons Learned
[What worked, what didn't]

## Future Recommendations
[Additional optimizations for later]
```

Track all changes and ensure each optimization is justified by measurable improvement.
