
import argparse
import person

def RunPopulationWorker(strategy, gender, n):
  # Initialize accumulators

  # Run n Person instantiations
  for i in range(n):
    p = person.Person(strategy, gender)
    p.LiveLife()

    # Merge in the results to our accumulators


def RunPopulation(strategy, gender, n):
  # Initialize accumulators for calculation of fitness function

  # Farm work out to worker process pool

  # Merge in the results to our accumulators

  # Calculate the fitness function

if __name__ == '__main__':
  # Set up flags
  
  # Run lives

  # Output reports
