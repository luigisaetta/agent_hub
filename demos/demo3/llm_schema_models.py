"""
Pydantic models mirroring the JSON schemas used in LLM extraction prompts.

Note:
- This module mirrors `proc_vendita.json` and is used at runtime.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict


#
# Schema: procedura_vendita_schema.json
#
class DatoCatastale(BaseModel):
    """Single cadastral data entry for one sale object."""

    model_config = ConfigDict(extra="forbid")
    dato_catastale: Optional[str]


class OggettoVendita(BaseModel):
    """Sale object details contained in a lot."""

    model_config = ConfigDict(extra="forbid")

    oggetto_vendita: str
    descrizione_dettagliata: str
    indirizzo_oggetto: Optional[str] = None
    dati_catastali: Optional[List[DatoCatastale]] = None
    stato: Optional[Literal["libero", "occupato", "non specificato", ""]]
    note: Optional[str] = None


class Lotto(BaseModel):
    """Single lot in the sale procedure."""

    model_config = ConfigDict(extra="forbid")

    lotto: str
    oggetti_vendita: List[OggettoVendita]
    valore_asta: str
    offerta_minima: Optional[str]
    offerta_minima_in_aumento: Optional[str]


class ProceduraVendita(BaseModel):
    """Root structured model for judicial sale procedure extraction."""

    model_config = ConfigDict(extra="forbid")

    tribunale: str
    numero_procedura: str
    tipo_vendita: str
    modalita_vendita: str
    termine_offerta: str
    professionista_delegato: str
    posta_certificata_professionista: Optional[str]
    iban_cauzione: str
    indirizzo_trasmissione_offerta: str
    lotti: List[Lotto]
