"""Every object content piece the object-pack search enumerates: the base
pieces plus the curated composites (ADR 0086)."""
from src.curriculum.library.objects.object_content import CONTENT_PIECES
from src.curriculum.library.objects.object_content_composite import COMPOSITE_PIECES

ALL_CONTENT_PIECES = {**CONTENT_PIECES, **COMPOSITE_PIECES}
