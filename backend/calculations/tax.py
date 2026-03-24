"""Deterministic personal income tax computations for FY 2025-26 (India).

All values are floats representing INR. No LLM usage permitted in this module.
"""
from __future__ import annotations

from typing import Dict, List

STANDARD_DEDUCTION_NEW_REGIME = 75_000.0
REBATE_87A_OLD_THRESHOLD = 700_000.0
REBATE_87A_OLD_AMOUNT = 25_000.0
REBATE_87A_NEW_THRESHOLD = 1_200_000.0


def calculate_hra_exemption(
    basic_salary: float,
    hra_received: float,
    rent_paid: float,
    is_metro_city: bool,
) -> float:
    """Compute HRA exemption under Section 10(13A).

    The exemption is the minimum of:
    1) Actual HRA received
    2) 50% of basic for metro cities, else 40%
    3) Rent paid minus 10% of basic

    Args:
        basic_salary: Annual basic salary.
        hra_received: Annual HRA received.
        rent_paid: Annual rent paid.
        is_metro_city: True if metro (Delhi, Mumbai, Kolkata, Chennai), else False.

    Returns:
        Exempt HRA amount (non-negative float).
    """

    if basic_salary <= 0 or hra_received <= 0 or rent_paid <= 0:
        return 0.0

    perc_basic = 0.5 if is_metro_city else 0.4
    basic_cap = basic_salary * perc_basic
    rent_minus_basic = rent_paid - 0.1 * basic_salary
    exemption = min(hra_received, basic_cap, rent_minus_basic)
    return max(0.0, exemption)


def _apply_old_regime_slabs(taxable: float) -> float:
    """Apply old regime slabs for FY 2025-26."""
    if taxable <= 0:
        return 0.0

    tax = 0.0
    remaining = taxable

    # 0 - 2.5L @ 0%
    slab_limit = 250_000.0
    if remaining > slab_limit:
        remaining -= slab_limit
    else:
        return tax

    # 2.5L - 5L @ 5%
    slab_range = 250_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.05
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 5L - 10L @ 20%
    slab_range = 500_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.20
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 10L+ @ 30%
    tax += remaining * 0.30
    return tax


def calculate_old_regime_tax(
    gross_income: float,
    hra_exemption: float,
    deduction_80c: float,
    deduction_80d: float,
    nps_80ccd_1b: float,
    home_loan_interest: float,
    other_deductions: float,
) -> Dict[str, float | Dict[str, float]]:
    """Compute total tax under old regime for FY 2025-26.

    Args:
        gross_income: Total income before exemptions/deductions.
        hra_exemption: Exempt HRA portion (from calculate_hra_exemption).
        deduction_80c: Section 80C deductions (cap assumed handled externally).
        deduction_80d: Section 80D deductions (health insurance premium).
        nps_80ccd_1b: Additional NPS deduction under 80CCD(1B).
        home_loan_interest: Deduction for self-occupied home loan interest (up to limits externally enforced).
        other_deductions: Any other deductions (e.g., 80E, 80TTA).

    Returns:
        Dict with taxable income, tax, rebate, cess, totals, and breakdown.
    """

    if gross_income <= 0:
        return {
            "taxable_income": 0.0,
            "tax_before_rebate": 0.0,
            "rebate_87a": 0.0,
            "cess": 0.0,
            "total_tax": 0.0,
            "effective_rate": 0.0,
            "deductions_breakdown": {},
        }

    deductions_breakdown = {
        "hra_exemption": max(0.0, hra_exemption),
        "80C": max(0.0, deduction_80c),
        "80D": max(0.0, deduction_80d),
        "80CCD_1B": max(0.0, nps_80ccd_1b),
        "home_loan_interest": max(0.0, home_loan_interest),
        "other": max(0.0, other_deductions),
    }

    total_deductions = sum(deductions_breakdown.values())
    taxable_income = max(0.0, gross_income - total_deductions)

    tax_before_rebate = _apply_old_regime_slabs(taxable_income)

    rebate_87a = REBATE_87A_OLD_AMOUNT if taxable_income <= REBATE_87A_OLD_THRESHOLD else 0.0
    tax_after_rebate = max(0.0, tax_before_rebate - rebate_87a)
    cess = tax_after_rebate * 0.04
    total_tax = tax_after_rebate + cess
    effective_rate = total_tax / gross_income if gross_income > 0 else 0.0

    return {
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate_87a,
        "cess": cess,
        "total_tax": total_tax,
        "effective_rate": effective_rate,
        "deductions_breakdown": deductions_breakdown,
    }


def _apply_new_regime_slabs(taxable: float) -> float:
    """Apply new regime slabs for FY 2025-26 (post-Budget 2025)."""
    if taxable <= 0:
        return 0.0

    tax = 0.0
    remaining = taxable

    # 0 - 4L @ 0%
    slab_limit = 400_000.0
    if remaining > slab_limit:
        remaining -= slab_limit
    else:
        return tax

    # 4L - 8L @ 5%
    slab_range = 400_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.05
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 8L - 12L @ 10%
    slab_range = 400_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.10
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 12L - 16L @ 15%
    slab_range = 400_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.15
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 16L - 20L @ 20%
    slab_range = 400_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.20
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 20L - 24L @ 25%
    slab_range = 400_000.0
    taxable_slab = min(remaining, slab_range)
    tax += taxable_slab * 0.25
    remaining -= taxable_slab
    if remaining <= 0:
        return tax

    # 24L+ @ 30%
    tax += remaining * 0.30
    return tax


def calculate_new_regime_tax(gross_income: float) -> Dict[str, float | Dict[str, float]]:
    """Compute total tax under new regime for FY 2025-26.

    Applies standard deduction of ₹75,000 and rebate u/s 87A if taxable ≤ ₹12L.

    Args:
        gross_income: Total income before deductions.

    Returns:
        Dict with taxable income, tax, rebate, cess, totals, and breakdown.
    """

    if gross_income <= 0:
        return {
            "taxable_income": 0.0,
            "tax_before_rebate": 0.0,
            "rebate_87a": 0.0,
            "cess": 0.0,
            "total_tax": 0.0,
            "effective_rate": 0.0,
            "deductions_breakdown": {"standard_deduction": 0.0},
        }

    standard_deduction = STANDARD_DEDUCTION_NEW_REGIME
    taxable_income = max(0.0, gross_income - standard_deduction)

    tax_before_rebate = _apply_new_regime_slabs(taxable_income)

    rebate_87a = tax_before_rebate if taxable_income <= REBATE_87A_NEW_THRESHOLD else 0.0
    tax_after_rebate = max(0.0, tax_before_rebate - rebate_87a)
    cess = tax_after_rebate * 0.04
    total_tax = tax_after_rebate + cess
    effective_rate = total_tax / gross_income if gross_income > 0 else 0.0

    return {
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate_87a,
        "cess": cess,
        "total_tax": total_tax,
        "effective_rate": effective_rate,
        "deductions_breakdown": {"standard_deduction": standard_deduction},
    }


def compare_tax_regimes(
    gross_income: float,
    hra_exemption: float,
    deduction_80c: float,
    deduction_80d: float,
    nps_80ccd_1b: float,
    home_loan_interest: float,
) -> Dict[str, object]:
    """Compare old vs new regime and recommend the lower tax option.

    Args:
        gross_income: Total income before deductions.
        hra_exemption: Exempt HRA.
        deduction_80c: 80C claims.
        deduction_80d: 80D claims.
        nps_80ccd_1b: Additional NPS deduction.
        home_loan_interest: Self-occupied home loan interest deduction.

    Returns:
        Dict containing both regime results, recommendation, savings, and missed deductions.
    """

    old_regime = calculate_old_regime_tax(
        gross_income=gross_income,
        hra_exemption=hra_exemption,
        deduction_80c=deduction_80c,
        deduction_80d=deduction_80d,
        nps_80ccd_1b=nps_80ccd_1b,
        home_loan_interest=home_loan_interest,
        other_deductions=0.0,
    )
    new_regime = calculate_new_regime_tax(gross_income=gross_income)

    recommended = "old" if old_regime["total_tax"] <= new_regime["total_tax"] else "new"
    savings = abs(new_regime["total_tax"] - old_regime["total_tax"])

    missed_deductions: List[Dict[str, float]] = []
    # Check unused 80C room up to ₹1.5L
    if deduction_80c < 150_000.0:
        missed_deductions.append({"section": "80C", "available_amount": 150_000.0 - deduction_80c})
    # Check 80D if not claimed
    if deduction_80d <= 0:
        missed_deductions.append({"section": "80D", "available_amount": 50_000.0})
    # Check NPS 80CCD(1B) room up to ₹50k
    if nps_80ccd_1b < 50_000.0:
        missed_deductions.append({"section": "80CCD(1B)", "available_amount": 50_000.0 - nps_80ccd_1b})

    return {
        "old_regime": old_regime,
        "new_regime": new_regime,
        "recommended": recommended,
        "savings_by_choosing_recommended": savings,
        "missed_deductions": missed_deductions,
    }
