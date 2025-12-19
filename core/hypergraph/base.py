import uuid
from enum import Enum
from typing import Dict, Any, Set, Optional
import numpy as np

class NodeType(Enum):
    CONCEPT = "concept"
    ENTITY = "entity"
    TOKEN = "token"
    ICON = "icon"

class HyperNode:
    """
    Represents a node in the hypergraph.
    Optimized with __slots__ for memory efficiency.
    """
    __slots__ = ('id', 'type', 'properties', 'embeddings')

    def __init__(self,
                 node_type: NodeType,
                 properties: Optional[Dict[str, Any]] = None,
                 node_id: Optional[uuid.UUID] = None):
        self.id = node_id if node_id else uuid.uuid4()
        self.type = node_type
        self.properties = properties if properties else {}
        self.embeddings: Dict[str, np.ndarray] = {}

    def add_embedding(self, model_name: str, vector: np.ndarray):
        self.embeddings[model_name] = vector

    def __repr__(self):
        return f"<HyperNode id={self.id} type={self.type.value}>"

class HyperEdge:
    """
    Represents a hyperedge connecting multiple nodes.
    Optimized with __slots__ for memory efficiency.
    """
    __slots__ = ('id', 'nodes', 'label', 'properties', 'weight')

    def __init__(self,
                 nodes: Set[uuid.UUID],
                 label: str,
                 properties: Optional[Dict[str, Any]] = None,
                 weight: float = 1.0,
                 edge_id: Optional[uuid.UUID] = None):
        self.id = edge_id if edge_id else uuid.uuid4()
        self.nodes = nodes
        self.label = label
        self.properties = properties if properties else {}
        self.weight = weight

    def __repr__(self):
        return f"<HyperEdge id={self.id} label={self.label} nodes={len(self.nodes)}>"
