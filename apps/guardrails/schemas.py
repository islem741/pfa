# schemas.py
# Définit la structure EXACTE que le LLM doit retourner.
# Pydantic valide automatiquement chaque champ.
#
# Le LLM doit répondre avec ce JSON :
# {
#   "answer": "Django est un framework web.",
#   "confidence": 0.95,
#   "sources": ["doc1"],
#   "disclaimer": null
# }

from pydantic import BaseModel, Field, field_validator


class KnowledgeAnswer(BaseModel):

    answer: str = Field(
        ...,           # "..." = obligatoire
        min_length=1,
        description="La réponse à la question",
    )
    confidence: float = Field(
        ...,
        ge=0.0,        # ge = supérieur ou égal à 0
        le=1.0,        # le = inférieur ou égal à 1
        description="Niveau de certitude : 0.0 = pas sûr, 1.0 = certain",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Sources utilisées pour répondre",
    )
    disclaimer: str | None = Field(
        None,
        description="Ajouté automatiquement si la confiance est trop basse",
    )

    @field_validator("answer")
    @classmethod
    def answer_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La réponse ne peut pas être vide")
        return v