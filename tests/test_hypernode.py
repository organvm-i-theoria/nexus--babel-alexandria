import pytest
import uuid
import numpy as np
from core.hypergraph.base import HyperNode, NodeType

def test_hypernode_initialization():
    """Test that HyperNode initializes correctly."""
    node = HyperNode(node_type=NodeType.CONCEPT)
    assert isinstance(node.id, uuid.UUID)
    assert node.type == NodeType.CONCEPT

    # These should now trigger lazy initialization
    assert node.properties == {}
    assert node.embeddings == {}

def test_hypernode_lazy_initialization():
    """Test that properties and embeddings are lazily initialized."""
    node = HyperNode(node_type=NodeType.CONCEPT)

    # Check internal slots directly (should be None)
    assert node._properties is None
    assert node._embeddings is None

    # Access properties to trigger initialization
    _ = node.properties
    assert node._properties is not None
    assert node._properties == {}

    # Access embeddings to trigger initialization
    _ = node.embeddings
    assert node._embeddings is not None
    assert node._embeddings == {}

def test_hypernode_slots_optimization():
    """Test that HyperNode uses __slots__ and does not have __dict__."""
    node = HyperNode(node_type=NodeType.ENTITY)

    # Verify __slots__ exists
    assert hasattr(node, '__slots__')
    assert 'id' in node.__slots__
    assert 'type' in node.__slots__
    assert '_properties' in node.__slots__
    assert '_embeddings' in node.__slots__

    # Verify __dict__ does not exist (memory optimization)
    assert not hasattr(node, '__dict__')

    # Verify we cannot add arbitrary attributes
    with pytest.raises(AttributeError):
        node.new_attr = "this should fail"

def test_hypernode_embeddings():
    """Test that we can store numpy arrays in embeddings."""
    node = HyperNode(node_type=NodeType.TOKEN)
    embedding = np.array([0.1, 0.2, 0.3])
    node.embeddings['bert'] = embedding

    assert 'bert' in node.embeddings
    np.testing.assert_array_equal(node.embeddings['bert'], embedding)
