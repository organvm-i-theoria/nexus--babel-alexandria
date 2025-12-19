import uuid
import sys
import numpy as np
import pytest
from core.hypergraph.base import HyperNode, HyperEdge, NodeType

def test_hypernode_creation():
    node = HyperNode(NodeType.CONCEPT, {"name": "Test Node"})
    assert isinstance(node.id, uuid.UUID)
    assert node.type == NodeType.CONCEPT
    assert node.properties["name"] == "Test Node"
    assert node.embeddings == {}

def test_hypernode_embedding():
    node = HyperNode(NodeType.ENTITY)
    vector = np.array([0.1, 0.2, 0.3])
    node.add_embedding("bert", vector)
    assert "bert" in node.embeddings
    np.testing.assert_array_equal(node.embeddings["bert"], vector)

def test_hyperedge_creation():
    node_id1 = uuid.uuid4()
    node_id2 = uuid.uuid4()
    nodes = {node_id1, node_id2}
    edge = HyperEdge(nodes, "related_to", weight=0.8)

    assert isinstance(edge.id, uuid.UUID)
    assert edge.nodes == nodes
    assert edge.label == "related_to"
    assert edge.weight == 0.8

def test_slots_optimization():
    """Verify that __slots__ are effectively preventing dynamic attribute creation"""
    node = HyperNode(NodeType.TOKEN)
    with pytest.raises(AttributeError):
        node.new_attr = "should fail"

    edge = HyperEdge({uuid.uuid4()}, "link")
    with pytest.raises(AttributeError):
        edge.dynamic_attr = "should fail"

def test_memory_usage_comparison():
    """Demonstrate memory saving (theoretical check via slots presence)"""
    # It's hard to reliably test exact memory usage in unit tests across platforms,
    # but we can verify the class structure.
    assert hasattr(HyperNode, '__slots__')
    assert hasattr(HyperEdge, '__slots__')

    # Ensure __dict__ is NOT present
    node = HyperNode(NodeType.ICON)
    assert not hasattr(node, '__dict__')

    edge = HyperEdge({uuid.uuid4()}, "test")
    assert not hasattr(edge, '__dict__')
