"""ChromaDB loader for SEBI/tax rule knowledge base."""

import os
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB client
DB_DIR = Path(__file__).parent / "db"
DB_DIR.mkdir(exist_ok=True)

client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(DB_DIR),
        anonymized_telemetry=False,
    )
)


def initialize_knowledge_base():
    """Load tax and SEBI rules into ChromaDB on startup."""
    try:
        collection = client.get_collection("financial_rules")
    except ValueError:
        # Collection doesn't exist, create it
        collection = client.create_collection(
            name="financial_rules",
            metadata={"hnsw:space": "cosine"},
        )

        # Tax rules (FY 2025-26)
        tax_rules = [
            {
                "id": "tax_old_regime_slabs",
                "text": "Old tax regime FY 2025-26: 0-2.5L @ 0%, 2.5-5L @ 5%, 5-10L @ 20%, 10L+ @ 30%. Rebate u/s 87A: ₹25,000 if taxable ≤ ₹7L.",
                "category": "tax",
            },
            {
                "id": "tax_new_regime_slabs",
                "text": "New tax regime FY 2025-26: 0-4L @ 0%, 4-8L @ 5%, 8-12L @ 10%, 12-16L @ 15%, 16-20L @ 20%, 20-24L @ 25%, 24L+ @ 30%. Standard deduction ₹75,000. Rebate u/s 87A: full rebate if taxable ≤ ₹12L.",
                "category": "tax",
            },
            {
                "id": "hra_exemption_metro",
                "text": "HRA exemption (metro): min(HRA received, 50% of basic, rent paid - 10% of basic).",
                "category": "tax",
            },
            {
                "id": "section_80c",
                "text": "Section 80C: Life insurance, provident fund, PPF, ELSS, NSC, tuition fees. Max deduction ₹1.5L per annum.",
                "category": "deduction",
            },
            {
                "id": "section_80d",
                "text": "Section 80D: Health insurance premium for self and family. Max ₹25K (self+spouse), ₹50K (with parents).",
                "category": "deduction",
            },
            {
                "id": "section_80ccd_1b",
                "text": "Section 80CCD(1B): Additional NPS deduction. Max ₹50,000 per annum (outside 80C limit).",
                "category": "deduction",
            },
            {
                "id": "home_loan_interest",
                "text": "Section 24: Home loan interest on self-occupied property. Max ₹200,000 in old regime, no limit in new regime (but effectively capped by loan structure).",
                "category": "deduction",
            },
        ]

        # SEBI rules
        sebi_rules = [
            {
                "id": "sebi_portfolio_overlap",
                "text": "SEBI guidelines recommend: Portfolio overlap should not exceed 20%. Rebalance to reduce concentration risk and churn cost.",
                "category": "sebi",
            },
            {
                "id": "sebi_expense_ratio",
                "text": "SEBI mandated expense ratios: Direct equity funds typically 0.5-1.5%, Debt funds 0.3-0.8%. High ERs increase drag and reduce returns.",
                "category": "sebi",
            },
            {
                "id": "sebi_stcg_tax",
                "text": "Short-term capital gains on mutual funds (< 1 year): Taxed as income at slab rates. Avoid rebalancing within 1-year window to minimize STCG.",
                "category": "taxes",
            },
            {
                "id": "sebi_nps_withdrawal",
                "text": "NPS withdrawal: Up to 25% can be withdrawn tax-free at retirement. Remaining must be annuitized (mandatory annuity).",
                "category": "compliance",
            },
            {
                "id": "sebi_ppf_withdrawal",
                "text": "PPF withdrawal: After 7 years, user can withdraw up to 50% of balance. Maturity after 15 years with option to extend.",
                "category": "compliance",
            },
        ]

        # Add all documents
        for rule in tax_rules + sebi_rules:
            collection.add(
                ids=[rule["id"]],
                documents=[rule["text"]],
                metadatas=[{"category": rule["category"]}],
            )

    return collection


def get_collection():
    """Get or initialize knowledge base collection."""
    try:
        return client.get_collection("financial_rules")
    except ValueError:
        return initialize_knowledge_base()
