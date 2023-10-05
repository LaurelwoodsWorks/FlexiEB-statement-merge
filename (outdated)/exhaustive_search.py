
import pandas as pd
import csv
from copy import deepcopy
import os
from typing import Final, Tuple

from common import *


def search(info: dict, history: list) -> None:
    # NOTE: {statement} plays a role as consumer
    for statement, row in info.items():

        # When have no producer statements
        if len(row[PRODUCER_STATEMENTS]) == 0: continue   
        

        # Recursively search on all of the producer statements
        for producer_statement in row[PRODUCER_STATEMENTS]:
            producer_statement = str(producer_statement)
            merge_statement, merge_row = merge(info, producer_statement, statement)
            # print(k, m)
            # if merge_statement == "EB-26-26-30-30-32-32-33-33":
            #     print(merge_row)


            # When satisfied the rule
            if merge_statement is not None:
                # Update info
                updated_info = deepcopy(info)

                updated_info[merge_statement] = merge_row
                update(updated_info, [producer_statement, statement], merge_statement)                
                # print(updated_info)


                # Write on history
                tmp = {}
                tmp["update"] = merge_statement
                tmp["result"] = updated_info
                tmp["total_benefit"] = compute_total_benefit(updated_info)
                tmp["next"] = []
                history.append(tmp)
                
                
                # Recursively proceed search
                # NOTE: Terminal condition is 
                # when there is no producer statement. 
                search(updated_info, tmp["next"])



def is_duplicated(target_list: list, target_row: dict) -> bool:
    '''
    {target_list} : list of statement info for check duplicate
    {target_row} : target row for check
    '''
    statements = list(target_row.keys())

    for l_row in target_list:
        l_statements = list(l_row.keys())

        if len(l_statements) != len(statements):
            continue
        
        matched = True
        for l, s in zip(sorted(l_statements), sorted(statements)):  # Are statements info already sorted for sure?
            if l != s:
                matched = False
                break
        
        if matched: return True
    
    return False



def categorically_extract_terminal_node(tree: dict, result: dict[str, list]) -> None:
    '''
    Return a dict 
        key: total_benefit
        value: list of statements info
    '''
    if len(tree['next']) == 0:
        if tree['total_benefit'] not in result:
            result[tree['total_benefit']] = []
        
        if len(result[tree['total_benefit']]) < 0 or \
            (not is_duplicated(result[tree['total_benefit']], tree['result'])):
            result[tree['total_benefit']].append(tree['result'])
    
    for subtree in tree['next']:
        categorically_extract_terminal_node(subtree, result)


def save(target_list: list, total_benefit: int, procedure: str, info_name: str) -> None:    
    for i, category in enumerate(target_list):
        rows = []
        for statement in category:
            
            producer_statement = to_string(category[statement][PRODUCER_STATEMENTS])
            consumer_statement = to_string(category[statement][CONSUMER_STATEMENTS])
            cost = category[statement][COST]
            result_size = category[statement][RESULT_SIZE]
            fragments = to_string(category[statement][FRAGMENTS])

            if len(category[statement]) > 5:
                consist = to_string(category[statement][CONSIST])
                benefit = category[statement][BENEFIT]
            else:
                consist = None
                benefit = None

            row = [
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
            rows.append(row)
        
        save_csv(rows, str(i), info_name, f"es/{total_benefit}")


def main(name):
    # original = load(os.path.join("input", name + ".csv"))
    original = load(os.path.join("input", "Statement-Information_1", name + ".csv"))

    search_result = {}
    search_result["next"] = []
    search(original, search_result["next"])

    result = {}
    categorically_extract_terminal_node(search_result, result)

    # Sort resulting statements info list with total_benefit in descending order
    result = dict(sorted(result.items(), reverse=True))

    best_benefit = next(iter(result))
    best_benefit_list = result[best_benefit]

    save(best_benefit_list, best_benefit, "5", name)


def benchmark(name):
    # import timeit
    # t = timeit.repeat(main, repeat=2, number=1)
    # print(t)

    # with open("analysis/es_benchmark.txt", "w") as f:
    #     for b in t:
    #         f.write(str(t))
    #         f.write("\n")

    import time
    benchmark = []
    for i in range(5):
        t = time.time()
        main(name)
        result = time.time() - t
        print(result)
        benchmark.append(result)

    with open("analysis/es_benchmark.txt", "w") as f:
        for b in benchmark:
            f.write(str(b))
            f.write("\n")


if __name__ == "__main__":
    # name = "Procedure-2"
    # main(name)    

    i = 7
    name = "Procedure-" + str(i)
    original = load(os.path.join("input", "Statement-Information_1", name + ".csv"))

    search_result = {}
    search_result["next"] = []
    search(original, search_result["next"])

    result = {}
    categorically_extract_terminal_node(search_result, result)

    # Sort resulting statements info list with total_benefit in descending order
    result = dict(sorted(result.items(), reverse=True))

    best_benefit = next(iter(result))
    best_benefit_list = result[best_benefit]

    # save(best_benefit_list, best_benefit, str(i), name)