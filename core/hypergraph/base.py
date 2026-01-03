from enum import Enum
from typing import Dict, Any, Optional
import uuid
import numpy as np

class NodeType(Enum):
    CONCEPT = "concept"
    ENTITY = "entity"
    TOKEN = "token"
    ICON = "icon"

class HyperNode:
    """
    A node in the hypergraph.

    Optimized for memory usage using __slots__ and lazy initialization.
    """
    __slots__ = ('id', 'type', '_properties', '_embeddings')

    def __init__(
        self,
        node_type: NodeType,
        properties: Optional[Dict[str, Any]] = None,
        node_id: Optional[uuid.UUID] = None
    ):
        self.id = node_id if node_id else uuid.uuid4()
        self.type = node_type
        self._properties = properties
        self._embeddings: Optional[Dict[str, np.ndarray]] = None

    @property
    def properties(self) -> Dict[str, Any]:
        if self._properties is None:
            self._properties = {}
        return self._properties

    @properties.setter
    def properties(self, value: Dict[str, Any]):
        self._properties = value

    @property
    def embeddings(self) -> Dict[str, np.ndarray]:
        if self._embeddings is None:
            self._embeddings = {}
        return self._embeddings

    @embeddings.setter
    def embeddings(self, value: Dict[str, np.ndarray]):
        self._embeddings = value
