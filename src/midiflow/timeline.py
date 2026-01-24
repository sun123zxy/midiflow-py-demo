from pydantic import BaseModel, Field

class ProgramChange(BaseModel):
    """MIDI program change (instrument selection)."""
    program: int = Field(default=0, ge=0, le=127)