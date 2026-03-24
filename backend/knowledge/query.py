"""RAG query interface for regulatory and tax rule lookups."""

from typing import List, Dict
from .loader import get_collection


class RegulatoryQuery:
    """Query financial rules via RAG."""

    def __init__(self):
        self.collection = get_collection()

    def query_tax_rules(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Find relevant tax rules via semantic search."""
        results = self.collection.query(
            query_texts=[query],
            where={"category": {"$eq": "tax"}},
            n_results=n_results,
        )

        return self._format_results(results)

    def query_deductions(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Find relevant deduction rules."""
        results = self.collection.query(
            query_texts=[query],
            where={"category": {"$eq": "deduction"}},
            n_results=n_results,
        )
        return self._format_results(results)

    def query_sebi_compliance(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Find SEBI compliance guidelines."""
        results = self.collection.query(
            query_texts=[query],
            where={"category": {"$in": ["sebi", "compliance"]}},
            n_results=n_results,
        )
        return self._format_results(results)

    def query_all_rules(self, query: str, n_results: int = 5) -> List[Dict[str, str]]:
        """Search across all rules."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        return self._format_results(results)

    @staticmethod
    def _format_results(results) -> List[Dict[str, str]]:
        """Format ChromaDB results."""
        formatted = []
        if results and results.get("documents"):
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                formatted.append({"rule": doc, "category": metadata.get("category", "unknown")})
        return formatted

    def validate_portfolio_overlap(self, overlap_percentage: float) -> Dict[str, any]:
        """Check portfolio overlap against SEBI norms."""
        sebi_rules = self.query_sebi_compliance("portfolio overlap", n_results=1)
        
        flag = overlap_percentage > 20.0
        return {
            "is_compliant": not flag,
            "overlap_percentage": overlap_percentage,
            "guideline": sebi_rules[0]["rule"] if sebi_rules else "",
            "action": "Rebalance to reduce overlap" if flag else "Portfolio diversification acceptable",
        }

    def validate_expense_ratio(self, average_er: float) -> Dict[str, any]:
        """Check if expense ratios are within acceptable range."""
        sebi_rules = self.query_sebi_compliance("expense ratio", n_results=1)
        
        flag = average_er > 1.5  # Average ER exceeds typical equity fund ER
        return {
            "is_compliant": not flag,
            "average_expense_ratio": average_er,
            "guideline": sebi_rules[0]["rule"] if sebi_rules else "",
            "action": "Consider lower-cost funds" if flag else "Expense ratios acceptable",
        }
