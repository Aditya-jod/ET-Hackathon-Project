"""Unit tests for tax and FIRE calculations."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pytest

# Ensure project root on path for direct test execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.calculations.tax import (  # type: ignore  # noqa: E402
    calculate_hra_exemption,
    calculate_old_regime_tax,
    calculate_new_regime_tax,
    compare_tax_regimes,
)
from backend.calculations.investments import (  # type: ignore  # noqa: E402
    calculate_fire_plan,
)


def test_tax_edge_case_old_vs_new_regime():
    """Validate tax comparison for provided edge profile."""

    basic_salary = 1_800_000.0
    hra_received = 360_000.0
    rent_paid = 300_000.0
    gross_income = basic_salary + hra_received

    hra_exempt = calculate_hra_exemption(
        basic_salary=basic_salary,
        hra_received=hra_received,
        rent_paid=rent_paid,
        is_metro_city=True,
    )
    assert hra_exempt == pytest.approx(120_000.0)

    comparison = compare_tax_regimes(
        gross_income=gross_income,
        hra_exemption=hra_exempt,
        deduction_80c=150_000.0,
        deduction_80d=0.0,
        nps_80ccd_1b=50_000.0,
        home_loan_interest=40_000.0,
    )

    old_total = comparison["old_regime"]["total_tax"]
    new_total = comparison["new_regime"]["total_tax"]

    # Exact computations based on FY 2025-26 slabs
    assert old_total == pytest.approx(366_600.0, rel=1e-3)
    assert new_total == pytest.approx(230_100.0, rel=1e-3)
    assert comparison["recommended"] == "new"
    assert new_total < old_total

    missed = comparison["missed_deductions"]
    assert any(item["section"] == "80D" for item in missed)


def test_fire_scenario_bounds():
    """Check FIRE calculations fall in expected ranges for scenario pack."""

    plan = calculate_fire_plan(
        age=34,
        income=2_400_000.0,
        monthly_expenses=120_000.0,
        existing_mf=1_800_000.0,
        existing_ppf=600_000.0,
        target_monthly_retirement=150_000.0,
        retire_at=50,
    )

    assert 55_000_000.0 <= plan["target_corpus"] <= 65_000_000.0
    assert 45_000.0 <= plan["monthly_sip_needed"] <= 75_000.0

    glide_equity = next(item for item in plan["asset_allocation_glidepath"] if item["age"] == 34)[
        "equity"
    ]
    assert 0.70 <= glide_equity <= 0.75
