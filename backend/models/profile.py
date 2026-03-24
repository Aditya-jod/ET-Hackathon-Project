"""Pydantic models for user financial profile."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class IncomeDetails(BaseModel):
    """Annual income breakdown."""

    basic_salary: float = Field(..., gt=0, description="Annual basic salary in INR")
    hra_received: float = Field(default=0.0, ge=0, description="Annual HRA received")
    other_income: float = Field(default=0.0, ge=0, description="Annual other income (e.g., rental, freelance)")
    is_metro_city: bool = Field(default=True, description="Whether salary is in metro city for HRA calc")


class DeductionsDetails(BaseModel):
    """Tax deductions claimed."""

    deduction_80c: float = Field(default=0.0, ge=0, le=150000.0, description="Section 80C deductions (max ₹1.5L)")
    deduction_80d: float = Field(default=0.0, ge=0, le=50000.0, description="Health insurance premium u/s 80D")
    nps_80ccd_1b: float = Field(
        default=0.0,
        ge=0,
        le=50000.0,
        description="Additional NPS deduction u/s 80CCD(1B) (max ₹50K)",
    )
    home_loan_interest: float = Field(default=0.0, ge=0, le=200000.0, description="Home loan interest deduction")
    other_deductions: float = Field(default=0.0, ge=0, description="Other eligible deductions")
    rent_paid_annual: float = Field(default=0.0, ge=0, description="Annual rent paid for HRA exemption calc")


class ExistingInvestments(BaseModel):
    """Already-owned investments."""

    mutual_funds_value: float = Field(default=0.0, ge=0, description="Current MF corpus value")
    ppf_balance: float = Field(default=0.0, ge=0, description="Current PPF balance")
    nps_balance: float = Field(default=0.0, ge=0, description="Current NPS corpus")
    fd_balance: float = Field(default=0.0, ge=0, description="Fixed deposits balance")
    stocks_value: float = Field(default=0.0, ge=0, description="Direct equity holdings value")
    gold_value: float = Field(default=0.0, ge=0, description="Gold/silver holdings value (grams×current rate)")
    real_estate_loans: float = Field(default=0.0, ge=0, description="Outstanding loans on property")
    other_debts: float = Field(default=0.0, ge=0, description="Credit card, personal loans, etc.")


class ExpenseProfile(BaseModel):
    """Monthly expense breakdown."""

    monthly_expenses: float = Field(..., gt=0, description="Total monthly living expenses")
    emergency_fund_months: float = Field(
        default=6.0,
        ge=3,
        le=12,
        description="Emergency fund coverage (months of expenses)",
    )


class LifeGoals(BaseModel):
    """User's financial goals."""

    retirement_age: int = Field(default=60, ge=40, le=75, description="Target retirement age")
    monthly_retirement_corpus: float = Field(
        default=None, description="Desired monthly expense in retirement (today's rupees)"
    )
    children_education_goal: float = Field(default=0.0, ge=0, description="Target corpus for children's education")
    home_purchase_goal: float = Field(default=0.0, ge=0, description="Target corpus for home purchase down payment")
    years_to_goal: int = Field(default=5, ge=1, le=10, description="Years to achieve home/education goal")
    risk_tolerance: str = Field(
        default="moderate",
        pattern="^(conservative|moderate|aggressive)$",
        description="Conservative, Moderate, or Aggressive",
    )


class UserProfile(BaseModel):
    """Complete user financial profile."""

    session_id: str = Field(..., description="Unique session identifier")
    age: int = Field(..., ge=18, le=100, description="Age in years")
    name: Optional[str] = Field(default=None, description="User's name (optional for privacy)")
    income: IncomeDetails
    deductions: DeductionsDetails
    expenses: ExpenseProfile
    investments: ExistingInvestments
    goals: LifeGoals

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123",
                "age": 34,
                "name": "Rajesh Kumar",
                "income": {
                    "basic_salary": 1800000,
                    "hra_received": 360000,
                    "other_income": 0,
                    "is_metro_city": True,
                },
                "deductions": {
                    "deduction_80c": 150000,
                    "deduction_80d": 25000,
                    "nps_80ccd_1b": 50000,
                    "home_loan_interest": 40000,
                    "other_deductions": 0,
                    "rent_paid_annual": 300000,
                },
                "expenses": {"monthly_expenses": 120000, "emergency_fund_months": 6},
                "investments": {
                    "mutual_funds_value": 1800000,
                    "ppf_balance": 600000,
                    "nps_balance": 300000,
                    "fd_balance": 500000,
                    "stocks_value": 0,
                    "gold_value": 0,
                    "real_estate_loans": 0,
                    "other_debts": 0,
                },
                "goals": {
                    "retirement_age": 50,
                    "monthly_retirement_corpus": 150000,
                    "children_education_goal": 2000000,
                    "home_purchase_goal": 0,
                    "years_to_goal": 5,
                    "risk_tolerance": "moderate",
                },
            }
        }

    @validator("monthly_retirement_corpus", always=True)
    def set_retirement_corpus(cls, v, values):
        if v is None and "expenses" in values:
            return values["expenses"].monthly_expenses * 1.25
        return v
