## 2024-05-23 - [Memory Optimization]
**Learning:** Using `__slots__` significantly reduces memory overhead for classes instantiated millions of times (like HyperGraph nodes/edges) by preventing the creation of `__dict__`.
**Action:** Always use `__slots__` for core data structures in the hypergraph layer.
