from typing import Literal

from pydantic import BaseModel

RecordType = Literal[
    "A",
    "AAAA",
    "CNAME",
    "MX",
    "NS",
    "OPENPGPKEY",
    "PTR",
    "TXT",
    "CAA",
    "CERT",
    "DNSKEY",
    "DS",
    "HTTPS",
    "LOC",
    "NAPTR",
    "SMIMEA",
    "SRV",
    "SSHFP",
    "SVCB",
    "TLSA",
    "URI",
]


class DNSRecord(BaseModel):
    id: str
    name: str
    type: RecordType
    content: str | None = None
