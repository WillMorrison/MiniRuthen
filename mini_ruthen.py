
import argparse
import collections
import csv
import multiprocessing
import os
import sys
import random
import math

from pyeasyga.pyeasyga import pyeasyga

import person
import utils
import world

StrategyBounds = collections.namedtuple("StrategyBounds",
                                        ["planned_retirement_age_min",
                                         "planned_retirement_age_max",
                                         "savings_threshold_min",
                                         "savings_threshold_max",
                                         "savings_rate_min",
                                         "savings_rate_max",
                                         "savings_rrsp_fraction_min",
                                         "savings_rrsp_fraction_max",
                                         "savings_tfsa_fraction_min",
                                         "savings_tfsa_fraction_max",
                                         "lico_target_fraction_min",
                                         "lico_target_fraction_max",
                                         "working_period_drawdown_tfsa_fraction_min",
                                         "working_period_drawdown_tfsa_fraction_max",
                                         "working_period_drawdown_nonreg_fraction_min",
                                         "working_period_drawdown_nonreg_fraction_max",
                                         "oas_bridging_fraction_min",
                                         "oas_bridging_fraction_max",
                                         "drawdown_ced_fraction_min",
                                         "drawdown_ced_fraction_max",
                                         "initial_cd_fraction_min",
                                         "initial_cd_fraction_max",
                                         "drawdown_preferred_rrsp_fraction_min",
                                         "drawdown_preferred_rrsp_fraction_max",
                                         "drawdown_preferred_tfsa_fraction_min",
                                         "drawdown_preferred_tfsa_fraction_max",
                                         "reinvestment_preference_tfsa_fraction_min",
                                         "reinvestment_preference_tfsa_fraction_max",])

DEFAULT_STRATEGY_BOUNDS = StrategyBounds(
    60, 65,  # planned_retirement_age
    0, 1000000,  # savings_threshold
    0, 0.5,  # savings_rate
    0, 1,  # savings_rrsp_fraction
    0, 1,  # savings_tfsa_fraction
    0, 5,  # lico_target_fraction
    0, 1,  # working_period_drawdown_tfsa_fraction
    0, 1,  # working_period_drawdown_nonreg_fraction
    0, 5,  # oas_bridging_fraction
    0, 1,  # drawdown_ced_fraction
    0, 1,  # initial_cd_fraction
    0, 1,  # drawdown_preferred_rrsp_fraction
    0, 1,  # drawdown_preferred_tfsa_fraction
    0, 1,  # reinvestment_preference_tfsa_fraction
    )

def RunPopulationWorker(strategy, gender, n, basic, real_values):
  # Initialize accumulators
  accumulators = utils.AccumulatorBundle(basic_only=basic)

  # Run n Person instantiations
  for i in range(n):
    p = person.Person(strategy, gender, basic, real_values)
    p.LiveLife()

    # Merge in the results to our accumulators
    accumulators.Merge(p.accumulators)

  return accumulators

def RunPopulation(strategy, gender, n, basic, real_values, use_multiprocessing):
  """Runs population multithreaded"""
  if not use_multiprocessing:
    return RunPopulationWorker(strategy, gender, n, basic, real_values)

  # Initialize accumulators for calculation of fitness function
  accumulators = utils.AccumulatorBundle(basic_only=basic)

  # Farm work out to worker process pool
  args = [(strategy, gender, n//os.cpu_count(), basic, real_values) for _ in range(os.cpu_count()-1)]
  args.append((strategy, gender, n - n//os.cpu_count() * (os.cpu_count()-1), basic, real_values))
  with multiprocessing.Pool() as pool:
    for result in [pool.apply_async(RunPopulationWorker, arg) for arg in args]:
      accumulators.Merge(result.get())

  return accumulators


def ValidateStrategy(strategy, bounds=DEFAULT_STRATEGY_BOUNDS):
  """Do bounds checking on a strategy and clip anything outside the valid range"""
  return person.Strategy(
      planned_retirement_age=int(min(max(bounds.planned_retirement_age_min, strategy.planned_retirement_age), bounds.planned_retirement_age_max)),
      savings_threshold=min(max(bounds.savings_threshold_min, strategy.savings_threshold), bounds.savings_threshold_max),
      savings_rate=min(max(bounds.savings_rate_min, strategy.savings_rate), bounds.savings_rate_max),
      savings_rrsp_fraction=min(max(bounds.savings_rrsp_fraction_min, strategy.savings_rrsp_fraction), bounds.savings_rrsp_fraction_max),
      savings_tfsa_fraction=min(max(bounds.savings_tfsa_fraction_min, strategy.savings_tfsa_fraction), bounds.savings_tfsa_fraction_max),
      lico_target_fraction=min(max(bounds.lico_target_fraction_min, strategy.lico_target_fraction), bounds.lico_target_fraction_max),
      working_period_drawdown_tfsa_fraction=min(max(bounds.working_period_drawdown_tfsa_fraction_min, strategy.working_period_drawdown_tfsa_fraction), bounds.working_period_drawdown_tfsa_fraction_max),
      working_period_drawdown_nonreg_fraction=min(max(bounds.working_period_drawdown_nonreg_fraction_min, strategy.working_period_drawdown_nonreg_fraction), bounds.working_period_drawdown_nonreg_fraction_max),
      oas_bridging_fraction=min(max(bounds.oas_bridging_fraction_min, strategy.oas_bridging_fraction), bounds.oas_bridging_fraction_max),
      drawdown_ced_fraction=min(max(bounds.drawdown_ced_fraction_min, strategy.drawdown_ced_fraction), bounds.drawdown_ced_fraction_max),
      initial_cd_fraction=min(max(bounds.initial_cd_fraction_min, strategy.initial_cd_fraction), bounds.initial_cd_fraction_max),
      drawdown_preferred_rrsp_fraction=min(max(bounds.drawdown_preferred_rrsp_fraction_min, strategy.drawdown_preferred_rrsp_fraction), bounds.drawdown_preferred_rrsp_fraction_max),
      drawdown_preferred_tfsa_fraction=min(max(bounds.drawdown_preferred_tfsa_fraction_min, strategy.drawdown_preferred_tfsa_fraction), bounds.drawdown_preferred_tfsa_fraction_max),
      reinvestment_preference_tfsa_fraction=min(max(bounds.reinvestment_preference_tfsa_fraction_min, strategy.reinvestment_preference_tfsa_fraction), bounds.reinvestment_preference_tfsa_fraction_max),
  )

def Optimize(gender, n, weights, population_size, max_generations, use_multiprocessing, bounds):
  """Run a genetic algorithm to optimize a strategy based on fitness function weights"""

  def individual_to_strategy(individual):
    return ValidateStrategy(person.Strategy(
        planned_retirement_age=bounds.planned_retirement_age_min + (bounds.planned_retirement_age_max - bounds.planned_retirement_age_min)*individual[0],
        savings_threshold=bounds.savings_threshold_min + (bounds.savings_threshold_max - bounds.savings_threshold_min)*individual[1],
        savings_rate=bounds.savings_rate_min + (bounds.savings_rate_max - bounds.savings_rate_min)*individual[2],
        savings_rrsp_fraction=bounds.savings_rrsp_fraction_min + (bounds.savings_rrsp_fraction_max - bounds.savings_rrsp_fraction_min)*individual[3],
        savings_tfsa_fraction=bounds.savings_tfsa_fraction_min + (bounds.savings_tfsa_fraction_max - bounds.savings_tfsa_fraction_min)*individual[4],
        lico_target_fraction=bounds.lico_target_fraction_min + (bounds.lico_target_fraction_max - bounds.lico_target_fraction_min)*individual[5],
        working_period_drawdown_tfsa_fraction=bounds.working_period_drawdown_tfsa_fraction_min + (bounds.working_period_drawdown_tfsa_fraction_max - bounds.working_period_drawdown_tfsa_fraction_min)*individual[6],
        working_period_drawdown_nonreg_fraction=bounds.working_period_drawdown_nonreg_fraction_min + (bounds.working_period_drawdown_nonreg_fraction_max - bounds.working_period_drawdown_nonreg_fraction_min)*individual[7],
        oas_bridging_fraction=bounds.oas_bridging_fraction_min + (bounds.oas_bridging_fraction_max - bounds.oas_bridging_fraction_min)*individual[8],
        drawdown_ced_fraction=bounds.drawdown_ced_fraction_min + (bounds.drawdown_ced_fraction_max - bounds.drawdown_ced_fraction_min)*individual[9],
        initial_cd_fraction=bounds.initial_cd_fraction_min + (bounds.initial_cd_fraction_max - bounds.initial_cd_fraction_min)*individual[10],
        drawdown_preferred_rrsp_fraction=bounds.drawdown_preferred_rrsp_fraction_min + (bounds.drawdown_preferred_rrsp_fraction_max - bounds.drawdown_preferred_rrsp_fraction_min)*individual[11],
        drawdown_preferred_tfsa_fraction=bounds.drawdown_preferred_tfsa_fraction_min + (bounds.drawdown_preferred_tfsa_fraction_max - bounds.drawdown_preferred_tfsa_fraction_min)*individual[12],
        reinvestment_preference_tfsa_fraction=bounds.reinvestment_preference_tfsa_fraction_min + (bounds.reinvestment_preference_tfsa_fraction_max - bounds.reinvestment_preference_tfsa_fraction_min)*individual[13],
        ),
        bounds)
 
  class MyGeneticAlgorithm(pyeasyga.GeneticAlgorithm):

    def run(self):
      """Run (solve) the Genetic Algorithm. Also a hack to output a csv table of generation fitness values as it goes."""
      self.create_first_generation()

      def OutputRow(i):
        mean = sum(individual.fitness for individual in self.current_generation)/len(self.current_generation)
        stdev = math.sqrt(sum((individual.fitness - mean)**2 for individual in self.current_generation)/len(self.current_generation))
        row = [
          i,
          self.best_individual()[0],
          mean,
          stdev,
          hash(tuple(self.best_individual()[1]))
          ]
        return ",".join(str(e) for e in row)

      print("Generation,Best Fitness,Fitness Mean,Fitness Stddev,Best Individual ID")
      for i in range(0, self.generations):
        print("%s" % OutputRow(i))
        self.create_next_generation()
      print("%s\n" % OutputRow(self.generations))
      
  ga = MyGeneticAlgorithm(weights, population_size=population_size, generations=max_generations, elitism=True, maximise_fitness=True)

  def create_individual(data):
    return [random.random() for _ in range(14)]
  ga.create_individual = create_individual

  def mutate(individual):
    for i in len(individual):
      individual[i] += random.gauss(0, 0.1)
  ga.mutate = mutate

  def crossover(parent1, parent2):
    children = []
    for gene_pair in zip(parent2, parent2):
      if random.randint(0, 1):
        children.append(gene_pair)
      else:
        children.append(reversed(gene_pair))
    child1, child2 = zip(*children)
    return child1, child2
  ga.crossover = crossover

  def fitness_function(individual, weights):
    strategy = individual_to_strategy(individual)
    accumulators = RunPopulation(strategy, gender, n, True, True, use_multiprocessing)
    return sum(component.contribution for component in GetFitnessFunctionCompositionTableRows(accumulators, weights))
  ga.fitness_function = fitness_function

  ga.run()

  fitness, best_individual = ga.best_individual()
  return individual_to_strategy(best_individual)


FitnessFunctionCompositionRow = collections.namedtuple("FitnessFunctionCompositionRow", ["component", "value", "stderr", "weight", "contribution"])

def GetFitnessFunctionCompositionTableRows(accumulators, weights):
  return [
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

def WriteFitnessFunctionCompositionTable(rows, out):
  writer = csv.writer(out, lineterminator='\n')
  writer.writerow(FitnessFunctionCompositionRow._fields)
  for row in rows:
    writer.writerow(row)

def WriteSummaryTable(gender, group_size, accumulators, weights, population_size, max_generations, accumulate_nominal, out):
  writer = csv.writer(out, lineterminator='\n')
  writer.writerow(("measure", "value"))
  writer.writerow(("Population Size", population_size))
  writer.writerow(("Max Generations", max_generations))
  writer.writerow(("Group Size", group_size))
  writer.writerow(("Fitness Function Value", sum(component.contribution for component in GetFitnessFunctionCompositionTableRows(accumulators, weights))))
  writer.writerow(("Gender", gender))
  writer.writerow(("Start Age", world.START_AGE))
  writer.writerow(("Nominal Accumulators", accumulate_nominal))
  writer.writerow(("Real Return on Investments", world.MEAN_INVESTMENT_RETURN))
  writer.writerow(("Age at Death", accumulators.age_at_death.mean))
  writer.writerow(("Average Years Worked", accumulators.years_worked_with_earnings.mean))
  writer.writerow(("Average Earnings Per Year Worked", accumulators.earnings_working.mean))
  writer.writerow(("Fraction of Persons Retiring Involuntarily", accumulators.fraction_persons_involuntarily_retired.mean))
  writer.writerow(("Fraction of Persons Dying Before Retiring", accumulators.fraction_persons_dying_before_retiring.mean))
  writer.writerow(("Average Annual Consumption", accumulators.lifetime_consumption_summary.mean))
  writer.writerow(("Average Annual EI/CPP Deductions in Working Period", accumulators.working_annual_ei_cpp_deductions.mean))
  writer.writerow(("Average Annual Taxes in Working Period", accumulators.working_taxes.mean))
  writer.writerow(("Average Annual Taxes in Retirement Period", accumulators.retirement_taxes.mean))
  writer.writerow(("Average Years with Positive Savings", accumulators.positive_savings_years.mean))
  writer.writerow(("Average Fraction of Earnings Saved", accumulators.fraction_earnings_saved.mean))
  writer.writerow(("Average Years Receiving EI Benefits", accumulators.years_receiving_ei.mean))
  writer.writerow(("Average Positive EI Benefits Received", accumulators.positive_ei_benefits.mean))
  writer.writerow(("Average Years Receiving GIS Benefits", accumulators.years_receiving_gis.mean))
  writer.writerow(("Average Positive GIS Benefits Level", accumulators.positive_gis_benefits.mean))
  writer.writerow(("Average Positive CPP Benefits Level", accumulators.positive_cpp_benefits.mean))
  writer.writerow(("Average Years Gross Income Below LICO", accumulators.years_income_below_lico.mean))
  writer.writerow(("Average Years with No Financial Assets at BoY", accumulators.years_with_no_assets.mean))
  writer.writerow(("Replacement Rate (Consumption Basis)", accumulators.period_consumption.Query([person.RETIRED, person.INVOLUNTARILY_RETIRED]).mean / accumulators.period_consumption.Query([person.EMPLOYED, person.UNEMPLOYED]).mean))
  writer.writerow(("Distributable Estate", accumulators.period_distributable_estate.Query([person.EMPLOYED, person.UNEMPLOYED, person.RETIRED, person.INVOLUNTARILY_RETIRED]).mean))
  writer.writerow(("Average Years With Negative Consumption", accumulators.years_with_negative_consumption.mean))

def WritePeriodSpecificTable(accumulators, out):
  def GetRow(name, accumulator):
    return [name,
            accumulator.Query([person.EMPLOYED, person.UNEMPLOYED, person.RETIRED, person.INVOLUNTARILY_RETIRED]).mean,
            accumulator.Query([person.EMPLOYED]).mean,
            accumulator.Query([person.UNEMPLOYED]).mean,
            accumulator.Query([person.RETIRED]).mean,
            accumulator.Query([person.INVOLUNTARILY_RETIRED]).mean]

  writer = csv.writer(out, lineterminator='\n')
  writer.writerow(("measure", "lifetime", "employed", "unemployed", "planned retirement", "unplanned retirement"))
  years_row = GetRow("Simulated years", accumulators.period_years)
  years_row[1] = None
  writer.writerow(years_row)
  writer.writerow(GetRow("Earnings", accumulators.period_earnings))
  writer.writerow(GetRow("CPP benefits", accumulators.period_cpp_benefits))
  writer.writerow(GetRow("OAS benefits", accumulators.period_oas_benefits))
  writer.writerow(GetRow("Taxable capital gains", accumulators.period_taxable_gains))
  writer.writerow(GetRow("GIS benefits", accumulators.period_gis_benefits))
  writer.writerow(GetRow("Social benefits repaid", accumulators.period_social_benefits_repaid))
  writer.writerow(GetRow("RRSP withdrawals", accumulators.period_rrsp_withdrawals))
  writer.writerow(GetRow("TFSA withdrawals", accumulators.period_tfsa_withdrawals))
  writer.writerow(GetRow("Nonregistered withdrawals", accumulators.period_nonreg_withdrawals))
  writer.writerow(GetRow("CPP contributions", accumulators.period_cpp_contributions))
  writer.writerow(GetRow("EI premiums", accumulators.period_ei_premiums))
  writer.writerow(GetRow("Taxable income", accumulators.period_taxable_income))
  writer.writerow(GetRow("Income tax", accumulators.period_income_tax))
  writer.writerow(GetRow("Sales tax", accumulators.period_sales_tax))
  writer.writerow(GetRow("Consumption", accumulators.period_consumption))
  writer.writerow(GetRow("RRSP savings", accumulators.period_rrsp_savings))
  writer.writerow(GetRow("TFSA savings", accumulators.period_tfsa_savings))
  writer.writerow(GetRow("Nonregistered savings", accumulators.period_nonreg_savings))
  writer.writerow(GetRow("Annual Fund Growth", accumulators.period_fund_growth))
  writer.writerow(GetRow("Gross Estate", accumulators.period_gross_estate))
  writer.writerow(GetRow("Estate Taxes", accumulators.period_estate_taxes))
  writer.writerow(GetRow("Executor and Funeral Cost", accumulators.period_executor_funeral_costs))
  writer.writerow(GetRow("Distributable Estate", accumulators.period_distributable_estate))

def WriteAgeSpecificTable(accumulators, group_size, out):
  def GetRow(age):
    return [age,
            accumulators.persons_alive_by_age.Query([age]).n,
            accumulators.gross_earnings_by_age.Query([age]).mean,
            accumulators.income_tax_by_age.Query([age]).mean,
            accumulators.ei_premium_by_age.Query([age]).mean,
            accumulators.cpp_contributions_by_age.Query([age]).mean,
            accumulators.sales_tax_by_age.Query([age]).mean,
            accumulators.ei_benefits_by_age.Query([age]).mean,
            accumulators.cpp_benefits_by_age.Query([age]).mean,
            accumulators.oas_benefits_by_age.Query([age]).mean,
            accumulators.gis_benefits_by_age.Query([age]).mean,
            accumulators.savings_by_age.Query([age]).mean,
            accumulators.rrsp_withdrawals_by_age.Query([age]).mean,
            accumulators.rrsp_assets_by_age.Query([age]).mean,
            accumulators.bridging_assets_by_age.Query([age]).mean,
            accumulators.tfsa_withdrawals_by_age.Query([age]).mean,
            accumulators.tfsa_assets_by_age.Query([age]).mean,
            accumulators.nonreg_withdrawals_by_age.Query([age]).mean,
            accumulators.nonreg_assets_by_age.Query([age]).mean,
            accumulators.consumption_by_age.Query([age]).mean,
            ]

  writer = csv.writer(out, lineterminator='\n')
  writer.writerow(("age", "Persons", "Gross Earnings", "Income Tax", "EI Premiums", "CPP Contrib", "Sales Tax", "EI Benefits", "CPP Benefits", "OAS Benefits", "GIS Benefits", "Total Savings", "RRSP Withdrawals", "RRSP Assets", "Bridging Assets", "TFSA Withdrawals", "TFSA Assets", "Non Registered Withdrawals", "NonRegistered Assets", "Consumption"))
  for age in range(world.START_AGE, max(world.MALE_MORTALITY.keys())+1):
    writer.writerow(GetRow(age))

def WriteStrategyTable(strategy, out):
  writer = csv.writer(out, lineterminator='\n')
  writer.writerow(("parameter", "value"))
  writer.writerow(("Planned Retirement Age", strategy.planned_retirement_age))
  writer.writerow(("Savings Threshold", strategy.savings_threshold)),
  writer.writerow(("Savings Rate", strategy.savings_rate)),
  writer.writerow(("Savings RRSP Fraction", strategy.savings_rrsp_fraction)),
  writer.writerow(("Savings TFSA Fraction", strategy.savings_tfsa_fraction)),
  writer.writerow(("LICO Target Fraction", strategy.lico_target_fraction)),
  writer.writerow(("Working Period Drawdown TFSA Fraction", strategy.working_period_drawdown_tfsa_fraction)),
  writer.writerow(("Working Period Drawdown NonReg Fraction", strategy.working_period_drawdown_nonreg_fraction)),
  writer.writerow(("OAS Bridging Fraction", strategy.oas_bridging_fraction)),
  writer.writerow(("Drawdown CED Fraction", strategy.drawdown_ced_fraction)),
  writer.writerow(("Initial CD Fraction", strategy.initial_cd_fraction)),
  writer.writerow(("Drawdown Preferred RRSP Fraction", strategy.drawdown_preferred_rrsp_fraction)),
  writer.writerow(("Drawdown Preferred TFSA Fraction", strategy.drawdown_preferred_tfsa_fraction)),
  writer.writerow(("Reinvestment Preference TFSA Fraction", strategy.reinvestment_preference_tfsa_fraction))


if __name__ == '__main__':
  # Set up flags
  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

  parser.add_argument('--number', help='Number of lives to simulate', type=int, default=1000)
  parser.add_argument('--gender', help='The gender of the people to simulate', choices=[person.MALE, person.FEMALE], default=person.FEMALE)
  parser.add_argument('--disable_multiprocessing', help='Only run on a single process', action='store_true', default=False)
  parser.add_argument('--basic_run', help='Only output the fitness function component and strategy tables', action='store_true', default=False)
  parser.add_argument('--accumulate_nominal_values', help='Store nominal dollar amounts in accumulators. Ignored for optimization runs.', action='store_true', default=False)

  # Strategy parameters (validation runs only)
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

  # Strategy parameter bounds
  parser.add_argument("--planned_retirement_age_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.planned_retirement_age_min)
  parser.add_argument("--planned_retirement_age_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.planned_retirement_age_max)
  parser.add_argument("--savings_threshold_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_threshold_min)
  parser.add_argument("--savings_threshold_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_threshold_max)
  parser.add_argument("--savings_rate_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_rate_min)
  parser.add_argument("--savings_rate_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_rate_max)
  parser.add_argument("--savings_rrsp_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_rrsp_fraction_min)
  parser.add_argument("--savings_rrsp_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_rrsp_fraction_max)
  parser.add_argument("--savings_tfsa_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_tfsa_fraction_min)
  parser.add_argument("--savings_tfsa_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.savings_tfsa_fraction_max)
  parser.add_argument("--lico_target_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.lico_target_fraction_min)
  parser.add_argument("--lico_target_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.lico_target_fraction_max)
  parser.add_argument("--working_period_drawdown_tfsa_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.working_period_drawdown_tfsa_fraction_min)
  parser.add_argument("--working_period_drawdown_tfsa_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.working_period_drawdown_tfsa_fraction_max)
  parser.add_argument("--working_period_drawdown_nonreg_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.working_period_drawdown_nonreg_fraction_min)
  parser.add_argument("--working_period_drawdown_nonreg_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.working_period_drawdown_nonreg_fraction_max)
  parser.add_argument("--oas_bridging_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.oas_bridging_fraction_min)
  parser.add_argument("--oas_bridging_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.oas_bridging_fraction_max)
  parser.add_argument("--drawdown_ced_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_ced_fraction_min)
  parser.add_argument("--drawdown_ced_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_ced_fraction_max)
  parser.add_argument("--initial_cd_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.initial_cd_fraction_min)
  parser.add_argument("--initial_cd_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.initial_cd_fraction_max)
  parser.add_argument("--drawdown_preferred_rrsp_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_preferred_rrsp_fraction_min)
  parser.add_argument("--drawdown_preferred_rrsp_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_preferred_rrsp_fraction_max)
  parser.add_argument("--drawdown_preferred_tfsa_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_preferred_tfsa_fraction_min)
  parser.add_argument("--drawdown_preferred_tfsa_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.drawdown_preferred_tfsa_fraction_max)
  parser.add_argument("--reinvestment_preference_tfsa_fraction_min", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.reinvestment_preference_tfsa_fraction_min)
  parser.add_argument("--reinvestment_preference_tfsa_fraction_max", help="strategy parameter bound", type=float, default=DEFAULT_STRATEGY_BOUNDS.reinvestment_preference_tfsa_fraction_max)

  # Fitness function component weights
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

  # Genetic algorithm parameters
  parser.add_argument("--optimize", help="Run the optimizer", action='store_true', default=False)
  parser.add_argument("--max_generations", help="Maximum genetic algorithm generations", type=int, default=10)
  parser.add_argument("--population_size", help="Individuals in the genetic algorithm's population", type=int, default=150)

  args = parser.parse_args()

  bounds = StrategyBounds(
      args.planned_retirement_age_min,
      args.planned_retirement_age_max,
      args.savings_threshold_min,
      args.savings_threshold_max,
      args.savings_rate_min,
      args.savings_rate_max,
      args.savings_rrsp_fraction_min,
      args.savings_rrsp_fraction_max,
      args.savings_tfsa_fraction_min,
      args.savings_tfsa_fraction_max,
      args.lico_target_fraction_min,
      args.lico_target_fraction_max,
      args.working_period_drawdown_tfsa_fraction_min,
      args.working_period_drawdown_tfsa_fraction_max,
      args.working_period_drawdown_nonreg_fraction_min,
      args.working_period_drawdown_nonreg_fraction_max,
      args.oas_bridging_fraction_min,
      args.oas_bridging_fraction_max,
      args.drawdown_ced_fraction_min,
      args.drawdown_ced_fraction_max,
      args.initial_cd_fraction_min,
      args.initial_cd_fraction_max,
      args.drawdown_preferred_rrsp_fraction_min,
      args.drawdown_preferred_rrsp_fraction_max,
      args.drawdown_preferred_tfsa_fraction_min,
      args.drawdown_preferred_tfsa_fraction_max,
      args.reinvestment_preference_tfsa_fraction_min,
      args.reinvestment_preference_tfsa_fraction_max,)

  strategy = ValidateStrategy(person.Strategy(
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
      reinvestment_preference_tfsa_fraction=args.reinvestment_preference_tfsa_fraction),
    bounds)
  
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

  if args.optimize:
    strategy = Optimize(args.gender, args.number, weights, args.population_size, args.max_generations, not args.disable_multiprocessing, bounds)

  # Run lives
  accumulators = RunPopulation(strategy, args.gender, args.number, args.basic_run, not args.accumulate_nominal_values, not args.disable_multiprocessing)

  # Output reports
  if not args.basic_run:
    WriteSummaryTable(args.gender, args.number, accumulators, weights, args.population_size if args.optimize else 1, args.max_generations if args.optimize else 1, args.accumulate_nominal_values, sys.stdout, )
    sys.stdout.write('\n')
  WriteStrategyTable(strategy, sys.stdout)
  sys.stdout.write('\n')
  fitness_fcn_comp_rows = GetFitnessFunctionCompositionTableRows(accumulators, weights)
  WriteFitnessFunctionCompositionTable(fitness_fcn_comp_rows, sys.stdout)
  if not args.basic_run:
    sys.stdout.write('\n')
    WritePeriodSpecificTable(accumulators, sys.stdout)
    sys.stdout.write('\n')
    WriteAgeSpecificTable(accumulators, args.number, sys.stdout)
