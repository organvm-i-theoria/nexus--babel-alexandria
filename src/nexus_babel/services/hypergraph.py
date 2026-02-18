from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neo4j import Driver, GraphDatabase


@dataclass
class LocalGraphCache:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)


class HypergraphProjector:
    def __init__(self, uri: str | None, username: str | None, password: str | None):  # allow-secret
        self._driver: Driver | None = None
        self.local = LocalGraphCache()
        if uri and username and password:
            self._driver = GraphDatabase.driver(uri, auth=(username, password))

    @property
    def enabled(self) -> bool:
        return self._driver is not None

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def project_document(self, document_id: str, document_payload: dict[str, Any], atoms: list[dict[str, Any]]) -> dict[str, Any]:
        doc_node_id = f"doc:{document_id}"
        self.local.nodes[doc_node_id] = {"label": "Document", **document_payload}

        atom_ids: list[str] = []
        for atom in atoms:
            atom_node_id = f"atom:{atom['id']}"
            atom_ids.append(atom_node_id)
            self.local.nodes[atom_node_id] = {"label": "Atom", **atom}
            self.local.edges.append(
                {
                    "type": "CONTAINS",
                    "from": doc_node_id,
                    "to": atom_node_id,
                    "metadata": {"atom_level": atom.get("atom_level")},
                }
            )

        if self._driver:
            with self._driver.session() as neo_session:
                neo_session.run(
                    "MERGE (d:Document {id: $id}) SET d += $props",
                    id=document_id,
                    props=document_payload,
                )
                for atom in atoms:
                    neo_session.run(
                        "MERGE (a:Atom {id: $aid}) SET a += $aprops "
                        "WITH a "
                        "MATCH (d:Document {id: $did}) "
                        "MERGE (d)-[:CONTAINS]->(a)",
                        aid=atom["id"],
                        aprops=atom,
                        did=document_id,
                    )

        return {"document_node_id": doc_node_id, "atom_node_ids": atom_ids}

    def integrity_for_document(self, document_id: str) -> dict[str, int]:
        doc_node_id = f"doc:{document_id}"
        if doc_node_id not in self.local.nodes:
            return {"document_nodes": 0, "atom_nodes": 0, "contains_edges": 0}

        edges = [edge for edge in self.local.edges if edge["from"] == doc_node_id and edge["type"] == "CONTAINS"]
        return {
            "document_nodes": 1,
            "atom_nodes": len(edges),
            "contains_edges": len(edges),
        }
