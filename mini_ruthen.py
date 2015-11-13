
import argparse
import multiprocessing
import os
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

  # Calculate the fitness function
  fitness = 0

  return (fitness, accumulators)

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

  # Run lives
  fitness, accumulators = RunPopulation(strategy, args.gender, args.number)

  # Output reports
  print("ConsumptionAvgLifetime", accumulators.lifetime_consumption_summary.mean)
  print("ConsumptionAvgWorking", accumulators.working_consumption_summary.mean)
  print("ConsumptionAvgRetired", accumulators.retired_consumption_summary.mean)
  print("ConsumptionAvgRetiredPreDisability", accumulators.pre_disability_retired_consumption_summary.mean)
  print("ConsumptionDiscountedLifetime", accumulators.discounted_lifetime_consumption_summary.mean)
  print("Consumption10PctLifetime", accumulators.lifetime_consumption_hist.Quantile(0.1))
  print("Consumption20PctLifetime", accumulators.lifetime_consumption_hist.Quantile(0.2))
  print("ConsumptionMedianLifetime", accumulators.lifetime_consumption_hist.Quantile(0.5))
  print("Consumption10PctRetired", accumulators.retired_consumption_hist.Quantile(0.1))
  print("Consumption20PctRetired", accumulators.retired_consumption_hist.Quantile(0.2))
  print("ConsumptionMedianRetired", accumulators.retired_consumption_hist.Quantile(0.5))
  print("StdConsumptionLifetime", accumulators.lifetime_consumption_summary.stddev)
  print("StdConsumptionWorking", accumulators.working_consumption_summary.stddev)
  print("StdConsumptionRetired", accumulators.retired_consumption_summary.stddev)


