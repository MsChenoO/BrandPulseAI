"""
Phase 4: Entity Extraction Service

Extracts entities (people, organizations, locations, products) from text using LLM.
"""

from typing import Dict, List, Optional, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    """Schema for extracted entities"""
    people: List[str] = Field(description="Names of people mentioned")
    organizations: List[str] = Field(description="Names of organizations/companies")
    locations: List[str] = Field(description="Locations/places mentioned")
    products: List[str] = Field(description="Products or services mentioned")
    technologies: List[str] = Field(description="Technologies or technical terms")


class EntityExtractionService:
    """Service for extracting named entities from text using LLM"""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.llm = ChatOllama(
            base_url=ollama_url,
            model=model,
            temperature=0,  # Deterministic for entity extraction
        )
        self.parser = JsonOutputParser(pydantic_object=ExtractedEntities)

        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting named entities from text.
Extract all entities from the given text and return them in the specified JSON format.
Only include entities that are explicitly mentioned. Return empty lists for categories with no entities.
Be precise and avoid duplicates."""),
            ("user", """Extract entities from this text:

Title: {title}
Content: {content}

{format_instructions}""")
        ])

    def extract_entities(self, title: str, content: Optional[str] = None) -> Optional[Dict[str, List[str]]]:
        """
        Extract entities from title and content

        Args:
            title: Text title
            content: Optional content text

        Returns:
            Dictionary with entity categories and lists of entities
            Returns None if extraction fails
        """
        try:
            # Prepare text
            content_text = content if content else ""

            # Create chain
            chain = self.prompt | self.llm | self.parser

            # Extract entities
            result = chain.invoke({
                "title": title,
                "content": content_text,
                "format_instructions": self.parser.get_format_instructions()
            })

            # Clean up result - remove empty categories
            cleaned_result = {
                key: [entity.strip() for entity in value if entity and entity.strip()]
                for key, value in result.items()
                if value  # Only include non-empty lists
            }

            return cleaned_result if cleaned_result else {}

        except Exception as e:
            print(f"✗ Entity extraction failed: {e}")
            return None

    def format_entities_for_display(self, entities: Dict[str, List[str]]) -> str:
        """
        Format extracted entities for human-readable display

        Args:
            entities: Dictionary of entity categories and lists

        Returns:
            Formatted string
        """
        if not entities:
            return "No entities extracted"

        lines = []
        category_labels = {
            "people": "People",
            "organizations": "Organizations",
            "locations": "Locations",
            "products": "Products",
            "technologies": "Technologies"
        }

        for category, entity_list in entities.items():
            if entity_list:
                label = category_labels.get(category, category.title())
                lines.append(f"{label}: {', '.join(entity_list)}")

        return "\n".join(lines) if lines else "No entities extracted"


# Global instance
_entity_service: Optional[EntityExtractionService] = None


def get_entity_extraction_service(
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3"
) -> EntityExtractionService:
    """Get or create global entity extraction service instance"""
    global _entity_service
    if _entity_service is None:
        _entity_service = EntityExtractionService(ollama_url, model)
    return _entity_service
