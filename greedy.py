
import pandas as pd
import csv
from copy import deepcopy
import os
from typing import Final, Tuple

from common import *

RESULT = None

def get_candidate_list(info: dict) -> list:
    # Sort candidate statements by expected benefits in descending order
    candidates_list = []
    for statement, row in info.items():
        # NOTE: statement is consumer

        if len(row[CONSUMER_STATEMENTS]) > 0: 
            # If statement is merge statement, 
            # also consider existing benefit
            if len(row) > 5:
                expected_benefit = row[RESULT_SIZE] + row[BENEFIT]
            else:
                expected_benefit = row[RESULT_SIZE]
                
            candidates_list.append([statement, expected_benefit])
    
    # Sort candidates by expected benefits in descending order 
    candidates_list = sorted(candidates_list, key=lambda x: -x[1]) 

    return candidates_list



def search(info: dict):
    '''
    Inner loop 
        for merging target statement with current largest expected benefit.

        {exhuasted_inner} is False
        when target statement was failed to merge (e.g. not passing rules).
    
    Outer loop 
        for when target statement was failed to merge
        proceed on statement with next largest expected benefit.

        {skip_outer} 
            True
                when greedy merged statement,
                thus no need to further iterate over other candidates
            False 
                when all the candidates are failed to merge
    '''

    # Get candidates list
    candidates_list = get_candidate_list(info)
    
    skip_outer = False
    
    # Outer loop for iterating over candidates
    for producer_statement, _ in candidates_list:
        target_row = info[producer_statement]
        
        exhuasted_inner = False
        updated_info = None
        
        # Inner loop for merging
        for consumer_statement in target_row[CONSUMER_STATEMENTS]:             
            # Merge
            merge_statement, merge_row = merge(info, producer_statement, consumer_statement)

            # When failed to satisfy the rules
            if merge_statement is None: continue

            # Update
            updated_info = deepcopy(info)

            update(updated_info, [producer_statement, consumer_statement], merge_statement)
            updated_info[merge_statement] = merge_row

            exhuasted_inner = True

            # from pprint import pprint
            # pprint(updated_info)
            # print("\n#--------------------------------------------------\n")
            break
        
        # When Inner loop ends with mergeing,
        # end Outer loop
        if exhuasted_inner: 
            skip_outer = True            
            break
    
    if skip_outer: 
        search(updated_info) # type:ignore
    else: 
        # print("\n# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
        # print(info)
        global RESULT
        RESULT = info
        # return info


def save(target_info: dict, total_benefit: int, procedure: str, info_name: str) -> None:   
    rows = [] 
    for statement, row in target_info.items():
        
        producer_statement = to_string(row[PRODUCER_STATEMENTS])
        consumer_statement = to_string(row[CONSUMER_STATEMENTS])
        cost = row[COST]
        result_size = row[RESULT_SIZE]
        fragments = to_string(row[FRAGMENTS])

        if len(row) > 5:
            consist = to_string(row[CONSIST])
            benefit = row[BENEFIT]
        else:
            consist = None
            benefit = None

        result_row = [
            procedure,
            statement,
            producer_statement,
            consumer_statement,
            cost,
            result_size,
            fragments,
            consist,
            benefit
        ]
        rows.append(result_row)
        
    save_csv(rows, str(total_benefit), info_name, "greedy")




def main(name: str):     
    # original = load(os.path.join("input", name + ".csv"))
    original = load(os.path.join("input", "Statement-Information_1", name + ".csv"))
    # result = search(original)
    search(original)

    save(RESULT, compute_total_benefit(RESULT), "10", name)  # type:ignore


def benchmark():
    import time

    NUM_TEST = 10
    result = []

    for i in range(NUM_TEST):
        t = time.time()
        main()
        r = time.time() - t
        print(r)
        result.append(r)

    # import timeit
    # t = timeit.repeat(main, number=100)
    # print(t)

    with open("analysis/greedy_benchmark.txt", "w") as f:
        for b in result:
            f.write(str(b))
            f.write("\n")




if __name__ == "__main__":
    # name = "Procedure-10"
    # main(name)

    fragment_name = "Fragment-Information.csv"

    name = "Experiment1"

    # i = 3
    for i in range(1, 7):
        statement_filename = "Procedure-" + str(i)
        
        statement_path = os.path.join("input", name, statement_filename + ".csv")
        fragment_path = os.path.join("input", fragment_name)

        original = load(statement_path, fragment_path)
        search(original)
        # print(RESULT)

        save(RESULT, compute_total_benefit(RESULT), str(i), statement_filename)  # type:ignore