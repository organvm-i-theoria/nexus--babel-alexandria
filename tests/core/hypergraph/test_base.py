import pytest
import sys
from uuid import uuid4
from core.hypergraph.base import HyperNode, HyperEdge, HyperNodeType

def test_hypernode_slots():
    """Verify HyperNode uses slots and has no __dict__."""
    node_id = uuid4()
    node = HyperNode(id=node_id, type=HyperNodeType.CONCEPT)

    assert not hasattr(node, '__dict__'), "HyperNode should not have __dict__"
    assert hasattr(node, '__slots__'), "HyperNode should have __slots__"

    # Verify we can access attributes
    assert node.id == node_id
    assert node.type == HyperNodeType.CONCEPT
    assert node.properties == {}
    assert node.embeddings == {}

def test_hyperedge_slots():
    """Verify HyperEdge uses slots and has no __dict__."""
    edge_id = uuid4()
    node_id = uuid4()
    edge = HyperEdge(id=edge_id, nodes={node_id}, label="related_to")

    assert not hasattr(edge, '__dict__'), "HyperEdge should not have __dict__"
    assert hasattr(edge, '__slots__'), "HyperEdge should have __slots__"

    # Verify we can access attributes
    assert edge.id == edge_id
    assert edge.label == "related_to"
    assert edge.weight == 1.0

def test_memory_optimization_check():
    """
    Demonstrate that objects with slots are smaller than objects without.
    This is a sanity check for the performance claim.
    """
    class NodeWithoutSlots:
        def __init__(self, id, type):
            self.id = id
            self.type = type
            self.properties = {}
            self.embeddings = {}

    node_id = uuid4()
    optimized_node = HyperNode(id=node_id, type=HyperNodeType.CONCEPT)
    standard_node = NodeWithoutSlots(id=node_id, type=HyperNodeType.CONCEPT)

    # Size of the object itself + size of __dict__ for standard_node
    # Note: getsizeof is not recursive, but it measures the object overhead.

    size_optimized = sys.getsizeof(optimized_node)
    size_standard = sys.getsizeof(standard_node) + sys.getsizeof(standard_node.__dict__)

    # On most systems, optimized should be significantly smaller
    # We log it to be sure
    print(f"\nSize of optimized HyperNode: {size_optimized} bytes")
    print(f"Size of standard Node (obj + dict): {size_standard} bytes")

    assert size_optimized < size_standard, "Optimized node should use less memory"
