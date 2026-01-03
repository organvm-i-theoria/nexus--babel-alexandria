import time
import sys
import gc
from core.hypergraph.base import HyperNode, NodeType

def benchmark():
    N = 100000

    print(f"Creating {N} nodes...")
    start_time = time.time()
    nodes = [HyperNode(NodeType.CONCEPT) for _ in range(N)]
    end_time = time.time()

    duration = end_time - start_time
    print(f"Creation time: {duration:.4f} seconds")

    # Measure approximate memory
    node = nodes[0]

    # Node struct size:
    node_size = sys.getsizeof(node)

    # Directly access internal slots.
    # We avoid getattr(node, 'properties') because that initializes it!
    # We use direct attribute access or getattr specific to _properties.

    props_internal = node._properties
    embeds_internal = node._embeddings

    props_size = sys.getsizeof(props_internal) if props_internal is not None else 0
    embeds_size = sys.getsizeof(embeds_internal) if embeds_internal is not None else 0

    if props_internal is None:
        print("Properties are lazily initialized (currently None)")
    else:
        print(f"Properties are initialized: {props_internal}")

    total_estimated = (node_size + props_size + embeds_size) * N
    print(f"Estimated unique memory for {N} nodes: {total_estimated / 1024 / 1024:.2f} MB")
    print(f"Per node overhead: {node_size} (struct) + {props_size} (props) + {embeds_size} (embeds) = {node_size + props_size + embeds_size} bytes")

if __name__ == "__main__":
    benchmark()
