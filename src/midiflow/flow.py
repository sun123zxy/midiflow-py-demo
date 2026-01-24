from typing import Annotated, Self
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator, PrivateAttr, validate_call
from .pattern import Pattern
from .modifier import Modifier


class PatternFlowNode(BaseModel):
    """A node in the PatternFlow graph.
    
    Contains a modifier and its input connections.
    """
    modifier: Modifier
    inputs: Annotated[list[str], Field(default_factory=list)]
    kwinputs: Annotated[dict[str, str | None], Field(default_factory=dict)]


class PatternFlow(BaseModel):
    """
    A directed acyclic graph (DAG) with nodes and edges representing flow synthesis of patterns.
    
    Execution and caching is handled privately. Only the core graph structure is exposed and serialized.

    You should never directly modify `nodes` after creation; use the provided methods instead.
    """
    nodes: Annotated[dict[str, PatternFlowNode], Field(default_factory=dict)]
    _outputs: Annotated[dict[str, set[str]], PrivateAttr()]
    _cache: Annotated[dict[str, Pattern | None], PrivateAttr()]

    def model_post_init(self, context) -> None:
        self._cache = {node_id: None for node_id in self.nodes}
        # Build outputs mapping
        self._outputs = {node_id: set() for node_id in self.nodes}
        for node_id, node in self.nodes.items():
            for input_id in node.inputs + list(node.kwinputs.values()):
                if input_id is not None:
                    self._outputs[input_id].add(node_id)

    def has_cycle(self, id: str | None = None) -> bool:
        """Check if there is a cycle in the graph.
        
        Args:
            id: Node ID to start checking from. If None, check all nodes.
            
        Returns:
            True if a cycle is detected, False otherwise.
        """
        if id is None:
            # Check all nodes without double counting
            visited_global: set[str] = set()
            for node_id in self.nodes:
                if node_id not in visited_global:
                    if self._has_cycle_from(node_id, set(), visited_global):
                        return True
            return False
        else:
            return self._has_cycle_from(id, set(), set())

    def _has_cycle_from(
        self, 
        current: str, 
        path: set[str], 
        visited_global: set[str]
    ) -> bool:
        """Helper method to detect cycles using DFS.
        
        Args:
            current: Current node being visited
            path: Nodes in current DFS path (for cycle detection)
            visited_global: All visited nodes across DFS calls (for efficiency)
            
        Returns:
            True if a cycle is detected from current node
        """
        if current not in self.nodes:
            # Invalid node reference, but not a cycle
            return False
            
        if current in path:
            # Found a cycle
            return True
            
        if current in visited_global:
            # Already checked this node in another path
            return False
        
        # Mark as visited
        path.add(current)
        visited_global.add(current)
        
        # Check all upstream nodes
        node = self.nodes[current]
        for input_id in node.inputs + list(node.kwinputs.values()):
            if input_id is not None and self._has_cycle_from(input_id, path, visited_global):
                return True
        
        # Remove from current path
        path.remove(current)
        return False

    @model_validator(mode='after')
    def validate_no_cycles(self) -> Self:
        """Pydantic validator to ensure no cycles exist in the graph."""
        if self.has_cycle():
            raise ValueError("PatternFlow contains cycles, which are not allowed")
        # Check id validity
        for node_id, node in self.nodes.items():
            for input_id in node.inputs + list(node.kwinputs.values()):
                if input_id is not None and input_id not in self.nodes:
                    raise KeyError(f"Node '{input_id}' referenced by node '{node_id}' not found")
        return self    

    def synth(self, id: str, force: bool = False) -> Pattern:
        """Synthesize the output pattern at node `id`. If `force` is True, will not use cache for this node.
        
        Recursively computes inputs if not cached. None in inputs goes with 
        default empty Pattern. Updates cache along the way.
        
        Args:
            id: Node ID to synthesize
            
        Returns:
            The synthesized Pattern
            
        Raises:
            KeyError: If node ID is not found
        """
        if id not in self.nodes:
            raise KeyError(f"Node ID '{id}' not found")
        
        # Check if already cached
        if not force and id in self._cache and self._cache[id] is not None:
            return self._cache[id]
        
        node = self.nodes[id]
        
        # Synthesize all inputs
        input_patterns: list[Pattern] = []
        for input_id in node.inputs:
            input_patterns.append(self.synth(input_id) if input_id is not None else Pattern())
        
        # Synthesize all keyword inputs
        kwinput_patterns: dict[str, Pattern] = {}
        for key, input_id in node.kwinputs.items():
            kwinput_patterns[key] = self.synth(input_id) if input_id is not None else Pattern()
        
        # Call the modifier's forward method
        result = node.modifier.forward(*input_patterns, **kwinput_patterns)
        
        # Cache the result
        self._cache[id] = result
        
        return result

    def populate(self, id: str) -> None:
        """Synthesize all downstream nodes of `id` (included) recursively, updating caches.
        
        Args:
            id: Node ID to start populating from
            
        Raises:
            KeyError: If node ID is not found
        """
        if id not in self.nodes:
            raise KeyError(f"Node ID '{id}' not found")
        
        # Synthesize this node
        self.synth(id, force=True)
        
        # Recursively populate all downstream nodes
        for downstream_id in self._outputs.get(id, set()):
            self.populate(downstream_id)

    def create(self, node: PatternFlowNode) -> str:
        """Create a new node and return its ID.
        
        Args:
            node: The PatternFlowNode to add
            
        Returns:
            The generated UUID for the new node
        """
        for input_id in node.inputs + list(node.kwinputs.values()):
            if input_id is not None and input_id not in self.nodes:
                raise KeyError(f"Node '{input_id}' referenced by the new node not found")
        
        node_id = str(uuid4())
        self.nodes[node_id] = node
        
        # Rebuild outputs to include the new node
        self._outputs[node_id] = set()
        for input_id in node.inputs + list(node.kwinputs.values()):
            if input_id is not None:
                self._outputs[input_id].add(node_id)
        
        return node_id

    def update(self, id: str, node: PatternFlowNode) -> Pattern:
        """Update node `id`, then populate downstream nodes.
        
        After updating the node, checks for cycles. If cycles are detected,
        reverts the inputs and raises ValueError.
        
        Args:
            id: Node ID to update
            node: New node configuration
            
        Returns:
            The synthesized Pattern for the updated node
            
        Raises:
            KeyError: If node ID is not found
            ValueError: If updating creates a cycle
        """
        if id not in self.nodes:
            raise KeyError(f"Node ID '{id}' not found")
        
        # Save old node for rollback
        old_node = self.nodes[id]
        
        # Update the node
        self.nodes[id] = node
        
        # Check for cycles
        if self.has_cycle(id):
            # Rollback
            self.nodes[id] = old_node
            raise ValueError(f"Updating node '{id}' would create a cycle, reverted changes")
        
        # Rebuild outputs to reflect new connections
        for input_id in old_node.inputs + list(old_node.kwinputs.values()):
            if input_id is not None:
                self._outputs[input_id].discard(id)
        
        for input_id in node.inputs + list(node.kwinputs.values()):
            if input_id is not None:
                self._outputs[input_id].add(id)
        
        # Populate this node and all downstream
        self.populate(id)
        
        return self._cache[id]

    def delete(self, id: str) -> None:
        """Delete node `id`, then populate downstream nodes.
        
        Args:
            id: Node ID to delete
            
        Raises:
            KeyError: If node ID is not found
        """
        if id not in self.nodes:
            raise KeyError(f"Node ID '{id}' not found")
        
        # Get downstream nodes before deleting
        downstream = self._outputs.get(id, set()).copy()

        # Rebuild outputs before deletion
        for input_id in self.nodes[id].inputs + list(self.nodes[id].kwinputs.values()):
            if input_id is not None:
                self._outputs[input_id].discard(id)
        
        # Delete the node
        if id in self.nodes: del self.nodes[id]
        if id in self._outputs: del self._outputs[id]
        if id in self._cache: del self._cache[id]
        
        # populate all former downstream nodes
        for downstream_id in downstream:
            self.populate(downstream_id)
