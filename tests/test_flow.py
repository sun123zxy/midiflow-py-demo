from fractions import Fraction
import pytest
from midiflow.flow import PatternFlow, PatternFlowNode
from midiflow.pattern import Pattern, Note
from midiflow.modifier import FromPattern, Union


def test_patternflownode_creation():
    """Test PatternFlowNode creation."""
    modifier = FromPattern(pattern=Pattern(notes={}, duration=Fraction(1)))
    node = PatternFlowNode(modifier=modifier, inputs=[], kwinputs={})
    assert node.modifier == modifier
    assert node.inputs == []
    assert node.kwinputs == {}


def test_patternflow_empty():
    """Test empty PatternFlow."""
    flow = PatternFlow(nodes={})
    assert len(flow.nodes) == 0
    assert not flow.has_cycle()


def test_patternflow_single_node():
    """Test PatternFlow with a single node."""
    pattern = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    node = PatternFlowNode(modifier=FromPattern(pattern=pattern))
    
    flow = PatternFlow(nodes={"n1": node})
    
    result = flow.synth("n1")
    assert result.duration == Fraction(1)
    assert Fraction(0) in result.notes


def test_patternflow_chain():
    """Test PatternFlow with chained nodes."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    p2 = Pattern(notes={Fraction(0): [Note(note=64)]}, duration=Fraction(1))
    
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    n2 = PatternFlowNode(modifier=FromPattern(pattern=p2))
    n3 = PatternFlowNode(modifier=Union(), inputs=["n1", "n2"])
    
    flow = PatternFlow(nodes={"n1": n1, "n2": n2, "n3": n3})
    
    result = flow.synth("n3")
    assert len(result.notes[Fraction(0)]) == 2  # Union combines both notes


def test_patternflow_cycle_detection():
    """Test cycle detection in PatternFlow."""
    p1 = Pattern(notes={}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1), inputs=["n2"])
    n2 = PatternFlowNode(modifier=Union(), inputs=["n1"])
    
    with pytest.raises(ValueError, match="cycles"):
        PatternFlow(nodes={"n1": n1, "n2": n2})


def test_patternflow_invalid_reference():
    """Test invalid node reference detection."""
    p1 = Pattern(notes={}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1), inputs=["nonexistent"])
    
    with pytest.raises(KeyError, match="nonexistent"):
        PatternFlow(nodes={"n1": n1})


def test_patternflow_create():
    """Test creating a new node."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    
    flow = PatternFlow(nodes={"n1": n1})
    
    p2 = Pattern(notes={Fraction(0): [Note(note=64)]}, duration=Fraction(1))
    n2 = PatternFlowNode(modifier=FromPattern(pattern=p2))
    
    new_id = flow.create(n2)
    assert new_id in flow.nodes
    assert len(flow.nodes) == 2


def test_patternflow_update():
    """Test updating a node."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    
    flow = PatternFlow(nodes={"n1": n1})
    
    p2 = Pattern(notes={Fraction(0): [Note(note=64)]}, duration=Fraction(1))
    n2 = PatternFlowNode(modifier=FromPattern(pattern=p2))
    
    result = flow.update("n1", n2)
    assert result.notes[Fraction(0)][0].note == 64


def test_patternflow_update_cycle_prevention():
    """Test that update prevents cycles."""
    p1 = Pattern(notes={}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    n2 = PatternFlowNode(modifier=Union(), inputs=["n1"])
    
    flow = PatternFlow(nodes={"n1": n1, "n2": n2})
    
    # Try to create cycle: n1 -> n2 -> n1
    n1_cyclic = PatternFlowNode(modifier=Union(), inputs=["n2"])
    
    with pytest.raises(ValueError, match="cycle"):
        flow.update("n1", n1_cyclic)
    
    # Verify rollback
    assert flow.nodes["n1"].modifier == n1.modifier


def test_patternflow_delete():
    """Test deleting a node."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    n2 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    
    flow = PatternFlow(nodes={"n1": n1, "n2": n2})
    
    flow.delete("n1")
    assert "n1" not in flow.nodes
    assert len(flow.nodes) == 1


def test_patternflow_caching():
    """Test that synth caches results."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    
    flow = PatternFlow(nodes={"n1": n1})
    
    result1 = flow.synth("n1")
    result2 = flow.synth("n1")
    
    # Should be cached (same object)
    assert result1 is result2


def test_patternflow_populate():
    """Test populate invalidates downstream caches."""
    p1 = Pattern(notes={Fraction(0): [Note(note=60)]}, duration=Fraction(1))
    p2 = Pattern(notes={Fraction(0): [Note(note=64)]}, duration=Fraction(1))
    
    n1 = PatternFlowNode(modifier=FromPattern(pattern=p1))
    n2 = PatternFlowNode(modifier=Union(), inputs=["n1"])
    
    flow = PatternFlow(nodes={"n1": n1, "n2": n2})
    
    # Populate cache
    flow.synth("n2")
    
    # Update n1 and populate
    n1_new = PatternFlowNode(modifier=FromPattern(pattern=p2))
    flow.update("n1", n1_new)
    
    # n2 should have updated result
    result = flow.synth("n2")
    assert result.notes[Fraction(0)][0].note == 64
