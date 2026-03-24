"""Deterministic investment and FIRE planning utilities.

All routines are pure Python math and safe for deterministic execution.
"""
from __future__ import annotations

from datetime import date
from math import pow
from typing import Dict, List

from scipy.optimize import brentq


def _npv(rate: float, cash_flows: List[float], dates: List[date]) -> float:
    """Net present value helper for XIRR."""
    if not cash_flows or not dates:
        return 0.0
    t0 = dates[0]
    npv_val = 0.0
    for cf, dt in zip(cash_flows, dates):
        days = (dt - t0).days
        npv_val += cf / pow(1 + rate, days / 365.0)
    return npv_val


def calculate_xirr(cash_flows: List[float], dates: List[date]) -> float:
    """Calculate the extended internal rate of return (XIRR).

    Cash flows must include at least one negative (investment) and one positive
    (redemption/current value). If all flows share the same sign or only one
    transaction exists, returns 0.0 to avoid invalid roots.

    Args:
        cash_flows: Sequence of cash flows; negatives for outflows, positives for inflows.
        dates: Corresponding dates for each cash flow (same length as cash_flows).

    Returns:
        Annualized XIRR as a decimal (e.g., 0.12 for 12%).
    """

    if len(cash_flows) != len(dates):
        raise ValueError("cash_flows and dates must have the same length")
    if len(cash_flows) < 2:
        return 0.0

    has_positive = any(cf > 0 for cf in cash_flows)
    has_negative = any(cf < 0 for cf in cash_flows)
    if not (has_positive and has_negative):
        return 0.0

    def npv_fn(rate: float) -> float:
        return _npv(rate, cash_flows, dates)

    # Try to bracket root between -99.99% and very high return.
    lower, upper = -0.9999, 10.0
    f_lower, f_upper = npv_fn(lower), npv_fn(upper)

    # Expand upper bound if needed to find sign change.
    attempts = 0
    while f_lower * f_upper > 0 and attempts < 10:
        upper *= 2
        f_upper = npv_fn(upper)
        attempts += 1

    if f_lower * f_upper > 0:
        # Fallback: cannot bracket root, return 0 to avoid failure.
        return 0.0

    return brentq(npv_fn, lower, upper)


def calculate_sip_future_value(
    monthly_amount: float,
    annual_return_rate: float,
    years: float,
) -> float:
    """Future value of a monthly SIP using compounding.

    Formula: P * [((1+r)^n - 1) / r] * (1+r), where r is monthly rate and n is total months.

    Args:
        monthly_amount: SIP contribution per month.
        annual_return_rate: Expected annual return (decimal, e.g., 0.11 for 11%).
        years: Investment duration in years.

    Returns:
        Future value at the end of the period.
    """

    if monthly_amount <= 0 or years <= 0:
        return 0.0

    monthly_rate = annual_return_rate / 12.0
    total_months = int(round(years * 12))
    if monthly_rate == 0:
        return monthly_amount * total_months

    growth_factor = pow(1 + monthly_rate, total_months)
    fv = monthly_amount * ((growth_factor - 1) / monthly_rate) * (1 + monthly_rate)
    return fv


def calculate_fire_corpus_target(
    monthly_expense_today: float,
    years_to_retire: float,
    years_in_retirement: float,
    inflation_rate: float = 0.06,
    safe_withdrawal_rate: float = 0.04,
) -> Dict[str, float]:
    """Estimate FIRE corpus required at retirement.

    Args:
        monthly_expense_today: Current monthly expense in today's rupees.
        years_to_retire: Years until retirement.
        years_in_retirement: Planned retirement duration (used for reporting).
        inflation_rate: Expected annual inflation (decimal).
        safe_withdrawal_rate: SWR used to size corpus (decimal).

    Returns:
        Dict with required corpus, expense at retirement, and implied years to deplete.
    """

    monthly_expense_at_retirement = monthly_expense_today * pow(1 + inflation_rate, years_to_retire)
    annual_expense_at_retirement = monthly_expense_at_retirement * 12
    corpus_needed = annual_expense_at_retirement / safe_withdrawal_rate if safe_withdrawal_rate > 0 else 0.0
    years_to_deplete = corpus_needed / annual_expense_at_retirement if annual_expense_at_retirement > 0 else 0.0

    return {
        "corpus_needed_at_retirement": corpus_needed,
        "monthly_expense_at_retirement": monthly_expense_at_retirement,
        "years_to_deplete": years_to_deplete,
    }


def calculate_fire_plan(
    age: int,
    income: float,
    monthly_expenses: float,
    existing_mf: float,
    existing_ppf: float,
    target_monthly_retirement: float,
    retire_at: int,
) -> Dict[str, object]:
    """Generate a simplified FIRE plan with glidepath and SIP need.

    Args:
        age: Current age in years.
        income: Annual income.
        monthly_expenses: Current monthly expenses.
        existing_mf: Current mutual fund corpus.
        existing_ppf: Current PPF corpus.
        target_monthly_retirement: Desired monthly draw in today's rupees.
        retire_at: Target retirement age.

    Returns:
        Dict with SIP need, trajectory, allocation glidepath, and insurance gap.
    """

    years_to_retire = max(0, retire_at - age)
    # Inflation-adjusted corpus target using desired retirement draw.
    corpus_info = calculate_fire_corpus_target(
        monthly_expense_today=target_monthly_retirement,
        years_to_retire=years_to_retire,
        years_in_retirement=35,
    )
    target_corpus = corpus_info["corpus_needed_at_retirement"]

    # Project existing investments (MF at 11%, PPF at 7%).
    mf_growth_rate = 0.11
    ppf_growth_rate = 0.07
    fv_existing_mf = existing_mf * pow(1 + mf_growth_rate, years_to_retire)
    fv_existing_ppf = existing_ppf * pow(1 + ppf_growth_rate, years_to_retire)
    fv_existing_total = fv_existing_mf + fv_existing_ppf

    # Monthly SIP needed to bridge gap at 11% expected return.
    expected_return = 0.11
    monthly_rate = expected_return / 12.0
    n_months = int(round(years_to_retire * 12))
    sip_growth_factor = pow(1 + monthly_rate, n_months)
    sip_factor = ((sip_growth_factor - 1) / monthly_rate) * (1 + monthly_rate) if monthly_rate != 0 and n_months > 0 else 0

    gap = max(0.0, target_corpus - fv_existing_total)
    monthly_sip_needed = (gap / sip_factor) if sip_factor > 0 else 0.0

    # Equity/debt/gold split for SIP
    sip_split = {
        "equity": monthly_sip_needed * 0.70,
        "debt": monthly_sip_needed * 0.20,
        "gold": monthly_sip_needed * 0.10,
    }

    # Estimate retirement age achievable with current monthly surplus (income - expenses).
    monthly_surplus = max(0.0, income / 12.0 - monthly_expenses)
    trajectory_age = retire_at
    if monthly_surplus > 0 and years_to_retire > 0:
        # Iterate yearly to find age when corpus meets target with surplus invested.
        curr_age = age
        curr_mf = existing_mf
        curr_ppf = existing_ppf
        while curr_age < 80:  # safety cap
            # Annual compounding and monthly contributions
            curr_mf = curr_mf * (1 + mf_growth_rate) + calculate_sip_future_value(monthly_surplus, expected_return, 1)
            curr_ppf = curr_ppf * (1 + ppf_growth_rate)
            curr_total = curr_mf + curr_ppf
            if curr_total >= target_corpus:
                trajectory_age = curr_age + 1
                break
            curr_age += 1
    else:
        trajectory_age = retire_at if fv_existing_total >= target_corpus else max(retire_at, age)

    shortfall_or_surplus = fv_existing_total - target_corpus

    # Glidepath: reduce equity after age 45 by 2% per year until 50% floor.
    glidepath: List[Dict[str, float]] = []
    equity_start = 0.75 if age < 45 else 0.70
    for yr in range(age, retire_at + 1):
        if yr <= 45:
            equity = equity_start
        else:
            reduction = (yr - 45) * 0.02
            equity = max(0.50, equity_start - reduction)
        debt = 1 - equity - 0.05  # reserve 5% for gold near retirement
        gold = 0.05
        glidepath.append({"age": yr, "equity": equity, "debt": debt, "gold": gold})

    insurance_gap = max(0.0, income * 10 - 0.0)

    return {
        "target_corpus": target_corpus,
        "monthly_sip_needed": monthly_sip_needed,
        "sip_split": sip_split,
        "current_trajectory_retire_age": trajectory_age,
        "shortfall_or_surplus": shortfall_or_surplus,
        "asset_allocation_glidepath": glidepath,
        "insurance_gap": insurance_gap,
        "existing_future_value": fv_existing_total,
        "corpus_details": corpus_info,
    }
