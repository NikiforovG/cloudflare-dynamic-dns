from pydantic import BaseModel


class DNSRecord(BaseModel):
    id: str
    name: str
    content: str | None = None
