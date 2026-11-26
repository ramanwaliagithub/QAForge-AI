"""Vector similarity, shared by duplicate detection and retrieval."""
import math


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors; 0.0 when either has no length (an empty embedding resembles nothing)."""
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0
