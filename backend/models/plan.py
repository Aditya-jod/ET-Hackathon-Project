"""Pydantic models for financial plans and recommendations."""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class TaxOptimizerResult(BaseModel):
    """Tax optimization analysis result."""

    old_regime_tax: float = Field(description="Tax under old regime")
    new_regime_tax: float = Field(description="Tax under new regime")
    recommended_regime: str = Field(pattern="^(old|new)$", description="Recommended tax regime")
    savings: float = Field(description="Tax savings if recommendation is followed")
    missed_deductions: List[Dict[str, float]] = Field(default_factory=list, description="Unclaimed deductions")
    effective_tax_rate: float = Field(description="Effective tax rate on gross income")


class FirePlanResult(BaseModel):
    """FIRE plan recommendation."""

    target_corpus_at_retirement: float = Field(description="Corpus needed at retirement")
    monthly_sip_needed: float = Field(description="Monthly SIP required")
    sip_equity_portion: float = Field(description="Equity allocation in SIP (₹)")
    sip_debt_portion: float = Field(description="Debt allocation in SIP (₹)")
    sip_gold_portion: float = Field(description="Gold allocation in SIP (₹)")
    current_trajectory_retire_age: int = Field(description="Age at which retirement goal is achieved at current rate")
    shortfall_or_surplus: float = Field(description="Current savings vs target gap")
    asset_allocation_glidepath: List[Dict[str, float]] = Field(description="Year-wise allocation (%)")
    insurance_gap: float = Field(description="Term insurance gap (required coverage)")
    emergency_fund_needed: float = Field(description="Required emergency fund corpus")


class PortfolioAnalysis(BaseModel):
    """MF portfolio X-ray results."""

    holdings: List[Dict] = Field(default_factory=list, description="Fund holdings breakdown")
    total_xirr: float = Field(description="Portfolio XIRR")
    overlap_percentage: float = Field(description="% portfolio overlap (same stocks across funds)")
    expense_ratio_drag: float = Field(description="Annual fee drag in absolute INR")
    top_overlapping_stocks: List[Dict[str, float]] = Field(default_factory=list, description="Most overlapped stocks")
    rebalancing_recommendation: str = Field(description="Action recommended for better diversification")
    stcg_impact: Dict[str, float] = Field(default_factory=dict, description="Short-term capital gains if rebalanced")


class FinancialPlan(BaseModel):
    """Complete financial plan output."""

    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_age: int
    retirement_age: int
    tax_analysis: TaxOptimizerResult
    fire_plan: FirePlanResult
    portfolio_analysis: Optional[PortfolioAnalysis] = None
    regulatory_flags: List[str] = Field(default_factory=list, description="SEBI/IT Act compliance notes")
    next_steps: List[str] = Field(default_factory=list, description="Action items for the user")
    disclaimer: str = Field(description="Mandatory SEBI disclaimer")

    class Config:
        json_schema_extra = {
            "description": "Complete financial plan including tax optimization, FIRE projections, and portfolio analysis"
        }
