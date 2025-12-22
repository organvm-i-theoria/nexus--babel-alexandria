from enum import Enum
from typing import Dict, Any, Set, Optional
from uuid import UUID
import numpy as np

class HyperNodeType(Enum):
    CONCEPT = "concept"
    ENTITY = "entity"
    TOKEN = "token"
    ICON = "icon"

class HyperNode:
    """
    HyperNode represents a node in the Hypergraph.

    Optimization: Uses __slots__ to significantly reduce memory footprint
    compared to __dict__, especially when millions of nodes are created.
    """
    __slots__ = ('id', 'type', 'properties', 'embeddings')

    def __init__(
        self,
        id: UUID,
        type: HyperNodeType,
        properties: Optional[Dict[str, Any]] = None,
        embeddings: Optional[Dict[str, np.ndarray]] = None
    ):
        self.id = id
        self.type = type
        self.properties = properties if properties is not None else {}
        self.embeddings = embeddings if embeddings is not None else {}

class HyperEdge:
    """
    HyperEdge represents an edge in the Hypergraph.

    Optimization: Uses __slots__ to reduce memory overhead.
    """
    __slots__ = ('id', 'nodes', 'label', 'properties', 'weight')

    def __init__(
        self,
        id: UUID,
        nodes: Set[UUID],
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ):
        self.id = id
        self.nodes = nodes
        self.label = label
        self.properties = properties if properties is not None else {}
        self.weight = weight
