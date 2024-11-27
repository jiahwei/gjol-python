from typing import Union, List, Optional
from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    version_id:int
    rank:int