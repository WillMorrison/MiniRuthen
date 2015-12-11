
import argparse
import collections
import csv
import multiprocessing
import os
import sys
import person
import utils

def RunPopulationWorker(strategy, gender, n):
  # Initialize accumulators
  accumulators = utils.AccumulatorBundle()

  # Run n Person instantiations
  for i in range(n):
    p = person.Person(strategy, gender)
    p.LiveLife()

    # Merge in the results to our accumulators
    accumulators.Merge(p.accumulators)

  return accumulators

def RunPopulation(strategy, gender, n):
  """Runs population multithreaded"""
  # Initialize accumulators for calculation of fitness function
  accumulators = utils.AccumulatorBundle()

  # Farm work out to worker process pool
  args = [(strategy, gender, n//os.cpu_count()) for _ in range(os.cpu_count()-1)]
  args.append((strategy, gender, n - n//os.cpu_count() * (os.cpu_count()-1)))
  with multiprocessing.Pool() as pool:
    sub_accumulators = pool.starmap(RunPopulationWorker, args)

  # Merge in the results to our accumulators
  for sub_accumulator in sub_accumulators:
    accumulators.Merge(sub_accumulator)

  return accumulators

FitnessFunctionCompositionRow = collections.namedtuple("FitnessFunctionCompositionRow", ["name", "value", "stderr", "weight", "contribution"])

def WriteFitnessFunctionCompositionTable(accumulators, weights, out):
  rows = [
    FitnessFunctionCompositionRow("ConsumptionAvgLifetime", accumulators.lifetime_consumption_summary.mean, accumulators.lifetime_consumption_summary.stderr, weights["ConsumptionAvgLifetime"], weights["ConsumptionAvgLifetime"] * accumulators.lifetime_consumption_summary.mean),
    FitnessFunctionCompositionRow("ConsumptionAvgWorking", accumulators.working_consumption_summary.mean, accumulators.working_consumption_summary.stderr, weights["ConsumptionAvgWorking"], weights["ConsumptionAvgWorking"] * accumulators.working_consumption_summary.mean),
    FitnessFunctionCompositionRow("ConsumptionAvgRetired", accumulators.retired_consumption_summary.mean, accumulators.retired_consumption_summary.stderr, weights["ConsumptionAvgRetired"], weights["ConsumptionAvgRetired"] * accumulators.retired_consumption_summary.mean),
    FitnessFunctionCompositionRow("ConsumptionAvgRetiredPreDisability", accumulators.pre_disability_retired_consumption_summary.mean, accumulators.pre_disability_retired_consumption_summary.stderr, weights["ConsumptionAvgRetiredPreDisability"], weights["ConsumptionAvgRetiredPreDisability"] * accumulators.pre_disability_retired_consumption_summary.mean),
    FitnessFunctionCompositionRow("ConsumptionDiscountedLifetime", accumulators.discounted_lifetime_consumption_summary.mean, accumulators.discounted_lifetime_consumption_summary.stderr, weights["ConsumptionDiscountedLifetime"], weights["ConsumptionDiscountedLifetime"] * accumulators.discounted_lifetime_consumption_summary.mean),
    FitnessFunctionCompositionRow("Consumption10PctLifetime", accumulators.lifetime_consumption_hist.Quantile(0.1), None, weights["Consumption10PctLifetime"], weights["Consumption10PctLifetime"] * accumulators.lifetime_consumption_hist.Quantile(0.1)),
    FitnessFunctionCompositionRow("Consumption20PctLifetime", accumulators.lifetime_consumption_hist.Quantile(0.2), None, weights["Consumption20PctLifetime"], weights["Consumption20PctLifetime"] * accumulators.lifetime_consumption_hist.Quantile(0.2)),
    FitnessFunctionCompositionRow("ConsumptionMedianLifetime", accumulators.lifetime_consumption_hist.Quantile(0.5), None, weights["ConsumptionMedianLifetime"], weights["ConsumptionMedianLifetime"] * accumulators.lifetime_consumption_hist.Quantile(0.5)),
    FitnessFunctionCompositionRow("Consumption10PctRetired", accumulators.retired_consumption_hist.Quantile(0.1), None, weights["Consumption10PctRetired"], weights["Consumption10PctRetired"] * accumulators.retired_consumption_hist.Quantile(0.1)),
    FitnessFunctionCompositionRow("Consumption20PctRetired", accumulators.retired_consumption_hist.Quantile(0.2), None, weights["Consumption20PctRetired"], weights["Consumption20PctRetired"] * accumulators.retired_consumption_hist.Quantile(0.2)),
    FitnessFunctionCompositionRow("ConsumptionMedianRetired", accumulators.retired_consumption_hist.Quantile(0.5), None, weights["ConsumptionMedianRetired"], weights["ConsumptionMedianRetired"] * accumulators.retired_consumption_hist.Quantile(0.5)),
    FitnessFunctionCompositionRow("StdConsumptionLifetime", accumulators.lifetime_consumption_summary.stddev, None, weights["StdConsumptionLifetime"], weights["StdConsumptionLifetime"] * accumulators.lifetime_consumption_summary.stddev),
    FitnessFunctionCompositionRow("StdConsumptionWorking", accumulators.working_consumption_summary.stddev, None, weights["StdConsumptionWorking"], weights["StdConsumptionWorking"] * accumulators.working_consumption_summary.stddev),
    FitnessFunctionCompositionRow("StdConsumptionRetired", accumulators.retired_consumption_summary.stddev, None, weights["StdConsumptionRetired"], weights["StdConsumptionRetired"] * accumulators.retired_consumption_summary.stddev),
    FitnessFunctionCompositionRow("EarningsAvgLateWorking", accumulators.earnings_late_working_summary.mean, accumulators.earnings_late_working_summary.stderr, weights["EarningsAvgLateWorking"], weights["EarningsAvgLateWorking"] * accumulators.earnings_late_working_summary.mean),
    FitnessFunctionCompositionRow("FractionPersonsRuined", accumulators.fraction_persons_ruined.mean, accumulators.fraction_persons_ruined.stderr, weights["FractionPersonsRuined"], weights["FractionPersonsRuined"] * accumulators.fraction_persons_ruined.mean),
    FitnessFunctionCompositionRow("FractionRetirementYearsRuined", accumulators.fraction_retirement_years_ruined.mean, accumulators.fraction_retirement_years_ruined.stderr, weights["FractionRetirementYearsRuined"], weights["FractionRetirementYearsRuined"] * accumulators.fraction_retirement_years_ruined.mean),
    FitnessFunctionCompositionRow("FractionRetirementYearsBelowYMPE", accumulators.fraction_retirement_years_below_ympe.mean, accumulators.fraction_retirement_years_below_ympe.stderr, weights["FractionRetirementYearsBelowYMPE"], weights["FractionRetirementYearsBelowYMPE"] * accumulators.fraction_retirement_years_below_ympe.mean),
    FitnessFunctionCompositionRow("FractionRetirementYearsBelowTwiceYMPE", accumulators.fraction_retirement_years_below_twice_ympe.mean, accumulators.fraction_retirement_years_below_twice_ympe.stderr, weights["FractionRetirementYearsBelowTwiceYMPE"], weights["FractionRetirementYearsBelowTwiceYMPE"] * accumulators.fraction_retirement_years_below_twice_ympe.mean),
    FitnessFunctionCompositionRow("FractionRetireesReceivingGIS", accumulators.fraction_retirees_receiving_gis.mean, accumulators.fraction_retirees_receiving_gis.stderr, weights["FractionRetireesReceivingGIS"], weights["FractionRetireesReceivingGIS"] * accumulators.fraction_retirees_receiving_gis.mean),
    FitnessFunctionCompositionRow("FractionRetirementYearsReceivingGIS", accumulators.fraction_retirement_years_receiving_gis.mean, accumulators.fraction_retirement_years_receiving_gis.stderr, weights["FractionRetirementYearsReceivingGIS"], weights["FractionRetirementYearsReceivingGIS"] * accumulators.fraction_retirement_years_receiving_gis.mean),
    FitnessFunctionCompositionRow("AverageBenefitsGIS", accumulators.benefits_gis.mean, accumulators.benefits_gis.stderr, weights["AverageBenefitsGIS"], weights["AverageBenefitsGIS"] * accumulators.benefits_gis.mean),
    FitnessFunctionCompositionRow("FractionRetireesEverBelowLICO", accumulators.fraction_retirees_ever_below_lico.mean, accumulators.fraction_retirees_ever_below_lico.stderr, weights["FractionRetireesEverBelowLICO"], weights["FractionRetireesEverBelowLICO"] * accumulators.fraction_retirees_ever_below_lico.mean),
    FitnessFunctionCompositionRow("FractionRetirementYearsBelowLICO", accumulators.fraction_retirement_years_below_lico.mean, accumulators.fraction_retirement_years_below_lico.stderr, weights["FractionRetirementYearsBelowLICO"], weights["FractionRetirementYearsBelowLICO"] * accumulators.fraction_retirement_years_below_lico.mean),
    FitnessFunctionCompositionRow("AverageLICOGapWorking", accumulators.lico_gap_working.mean, accumulators.lico_gap_working.stderr, weights["AverageLICOGapWorking"], weights["AverageLICOGapWorking"] * accumulators.lico_gap_working.mean),
    FitnessFunctionCompositionRow("AverageLICOGapRetired", accumulators.lico_gap_retired.mean, accumulators.lico_gap_retired.stderr, weights["AverageLICOGapRetired"], weights["AverageLICOGapRetired"] * accumulators.lico_gap_retired.mean),
    FitnessFunctionCompositionRow("FractionPersonsWithWithdrawalsBelowRetirementAssets", accumulators.fraction_persons_with_withdrawals_below_retirement_assets.mean, accumulators.fraction_persons_with_withdrawals_below_retirement_assets.stderr, weights["FractionPersonsWithWithdrawalsBelowRetirementAssets"], weights["FractionPersonsWithWithdrawalsBelowRetirementAssets"] * accumulators.fraction_persons_with_withdrawals_below_retirement_assets.mean),
    FitnessFunctionCompositionRow("FractionRetireesWithWithdrawalsBelowRetirementAssets", accumulators.fraction_retirees_with_withdrawals_below_retirement_assets.mean, accumulators.fraction_retirees_with_withdrawals_below_retirement_assets.stderr, weights["FractionRetireesWithWithdrawalsBelowRetirementAssets"], weights["FractionRetireesWithWithdrawalsBelowRetirementAssets"] * accumulators.fraction_retirees_with_withdrawals_below_retirement_assets.mean),
    FitnessFunctionCompositionRow("AverageLifetimeWithdrawalsLessSavings", accumulators.lifetime_withdrawals_less_savings.mean, accumulators.lifetime_withdrawals_less_savings.stderr, weights["AverageLifetimeWithdrawalsLessSavings"], weights["AverageLifetimeWithdrawalsLessSavings"] * accumulators.lifetime_withdrawals_less_savings.mean),
    FitnessFunctionCompositionRow("ConsumptionAvgRetirementBelowFractionAvgWorking", accumulators.retirement_consumption_less_working_consumption.mean, accumulators.retirement_consumption_less_working_consumption.stderr, weights["ConsumptionAvgRetirementBelowFractionAvgWorking"], weights["ConsumptionAvgRetirementBelowFractionAvgWorking"] * accumulators.retirement_consumption_less_working_consumption.mean),
    FitnessFunctionCompositionRow("AverageDistributableEstate", accumulators.distributable_estate.mean, accumulators.distributable_estate.stderr, weights["AverageDistributableEstate"], weights["AverageDistributableEstate"] * accumulators.distributable_estate.mean),
  ]

  writer = csv.writer(out)
  writer.writerow(FitnessFunctionCompositionRow._fields)
  for row in rows:
    writer.writerow(row)


if __name__ == '__main__':
  # Set up flags
  parser = argparse.ArgumentParser()

  parser.add_argument('--number', help='Number of lives to simulate', type=int, default=1000)
  parser.add_argument('--gender', help='The gender of the people to simulate', choices=[person.MALE, person.FEMALE], default=person.FEMALE)

  parser.add_argument("--planned_retirement_age", help="strategy parameter", type=int, default=65)
  parser.add_argument("--savings_threshold", help="strategy parameter", type=float, default=0)
  parser.add_argument("--savings_rate", help="strategy parameter", type=float, default=0.1)
  parser.add_argument("--savings_rrsp_fraction", help="strategy parameter", type=float, default=0.1)
  parser.add_argument("--savings_tfsa_fraction", help="strategy parameter", type=float, default=0.2)
  parser.add_argument("--lico_target_fraction", help="strategy parameter", type=float, default=1.0)
  parser.add_argument("--working_period_drawdown_tfsa_fraction", help="strategy parameter", type=float, default=0.5)
  parser.add_argument("--working_period_drawdown_nonreg_fraction", help="strategy parameter", type=float, default=0.5)
  parser.add_argument("--oas_bridging_fraction", help="strategy parameter", type=float, default=1.0)
  parser.add_argument("--drawdown_ced_fraction", help="strategy parameter", type=float, default=0.8)
  parser.add_argument("--initial_cd_fraction", help="strategy parameter", type=float, default=0.04)
  parser.add_argument("--drawdown_preferred_rrsp_fraction", help="strategy parameter", type=float, default=0.35)
  parser.add_argument("--drawdown_preferred_tfsa_fraction", help="strategy parameter", type=float, default=0.5)
  parser.add_argument("--reinvestment_preference_tfsa_fraction", help="strategy parameter", type=float, default=0.8)

  parser.add_argument("--consumption_avg_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_avg_working", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_avg_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_avg_retired_pre_disability", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_discounted_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_10pct_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_20pct_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_median_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_10pct_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_20pct_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_median_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--std_consumption_lifetime", help="fitness component weight", type=float, default=0)
  parser.add_argument("--std_consumption_working", help="fitness component weight", type=float, default=0)
  parser.add_argument("--std_consumption_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--earnings_avg_late_working", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_persons_ruined", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirement_years_ruined", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirement_years_below_ympe", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirement_years_below_twice_ympe", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirees_receiving_gis", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirement_years_receiving_gis", help="fitness component weight", type=float, default=0)
  parser.add_argument("--average_benefits_gis", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirees_ever_below_lico", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirement_years_below_lico", help="fitness component weight", type=float, default=0)
  parser.add_argument("--average_lico_gap_working", help="fitness component weight", type=float, default=0)
  parser.add_argument("--average_lico_gap_retired", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_persons_with_withdrawals_below_retirement_assets", help="fitness component weight", type=float, default=0)
  parser.add_argument("--fraction_retirees_with_withdrawals_below_retirement_assets", help="fitness component weight", type=float, default=0)
  parser.add_argument("--average_lifetime_withdrawals_less_savings", help="fitness component weight", type=float, default=0)
  parser.add_argument("--consumption_avg_retirement_below_fraction_avg_working", help="fitness component weight", type=float, default=0)
  parser.add_argument("--average_distributable_estate", help="fitness component weight", type=float, default=0)

  

  
  args = parser.parse_args()

  strategy = person.Strategy(
      planned_retirement_age=args.planned_retirement_age,
      savings_threshold=args.savings_threshold,
      savings_rate=args.savings_rate,
      savings_rrsp_fraction=args.savings_rrsp_fraction,
      savings_tfsa_fraction=args.savings_tfsa_fraction,
      lico_target_fraction=args.lico_target_fraction,
      working_period_drawdown_tfsa_fraction=args.working_period_drawdown_tfsa_fraction,
      working_period_drawdown_nonreg_fraction=args.working_period_drawdown_nonreg_fraction,
      oas_bridging_fraction=args.oas_bridging_fraction,
      drawdown_ced_fraction=args.drawdown_ced_fraction,
      initial_cd_fraction=args.initial_cd_fraction,
      drawdown_preferred_rrsp_fraction=args.drawdown_preferred_rrsp_fraction,
      drawdown_preferred_tfsa_fraction=args.drawdown_preferred_tfsa_fraction,
      reinvestment_preference_tfsa_fraction=args.reinvestment_preference_tfsa_fraction)
  
  weights = {
    "ConsumptionAvgLifetime": args.consumption_avg_lifetime,
    "ConsumptionAvgWorking": args.consumption_avg_working,
    "ConsumptionAvgRetired": args.consumption_avg_retired,
    "ConsumptionAvgRetiredPreDisability": args.consumption_avg_retired_pre_disability,
    "ConsumptionDiscountedLifetime": args.consumption_discounted_lifetime,
    "Consumption10PctLifetime": args.consumption_10pct_lifetime,
    "Consumption20PctLifetime": args.consumption_20pct_lifetime,
    "ConsumptionMedianLifetime": args.consumption_median_lifetime,
    "Consumption10PctRetired": args.consumption_10pct_retired,
    "Consumption20PctRetired": args.consumption_20pct_retired,
    "ConsumptionMedianRetired": args.consumption_median_retired,
    "StdConsumptionLifetime": args.std_consumption_lifetime,
    "StdConsumptionWorking": args.std_consumption_working,
    "StdConsumptionRetired": args.std_consumption_retired,
    "EarningsAvgLateWorking": args.earnings_avg_late_working,
    "FractionPersonsRuined": args.fraction_persons_ruined,
    "FractionRetirementYearsRuined": args.fraction_retirement_years_ruined,
    "FractionRetirementYearsBelowYMPE": args.fraction_retirement_years_below_ympe,
    "FractionRetirementYearsBelowTwiceYMPE": args.fraction_retirement_years_below_twice_ympe,
    "FractionRetireesReceivingGIS": args.fraction_retirees_receiving_gis,
    "FractionRetirementYearsReceivingGIS": args.fraction_retirement_years_receiving_gis,
    "AverageBenefitsGIS": args.average_benefits_gis,
    "FractionRetireesEverBelowLICO": args.fraction_retirees_ever_below_lico,
    "FractionRetirementYearsBelowLICO": args.fraction_retirement_years_below_lico,
    "AverageLICOGapWorking": args.average_lico_gap_working,
    "AverageLICOGapRetired": args.average_lico_gap_retired,
    "FractionPersonsWithWithdrawalsBelowRetirementAssets": args.fraction_persons_with_withdrawals_below_retirement_assets,
    "FractionRetireesWithWithdrawalsBelowRetirementAssets": args.fraction_retirees_with_withdrawals_below_retirement_assets,
    "AverageLifetimeWithdrawalsLessSavings": args.average_lifetime_withdrawals_less_savings,
    "ConsumptionAvgRetirementBelowFractionAvgWorking": args.consumption_avg_retirement_below_fraction_avg_working,
    "AverageDistributableEstate": args.average_distributable_estate,
  }

  # Run lives
  accumulators = RunPopulation(strategy, args.gender, args.number)

  # Output reports
  WriteFitnessFunctionCompositionTable(accumulators, weights, sys.stdout)
