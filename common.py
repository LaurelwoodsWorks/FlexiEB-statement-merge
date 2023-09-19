import pandas as pd
import csv
from copy import deepcopy
import os
from typing import Final, Tuple

# -----------------------------------------------------
# Constants

TOTAL_COST_SUM = 0          # For (temporary) A computation (obtained below)
TOTAL_NUM_FRAGMENTS = 0     # For (temporary) B computation #243

# Row Indices
PRODUCER_STATEMENTS: Final[int] = 0
CONSUMER_STATEMENTS: Final[int] = 1
COST: Final[int] = 2
RESULT_SIZE: Final[int] = 3
FRAGMENTS: Final[int] = 4
CONSIST: Final[int] = 5
BENEFIT: Final[int] = 6


# -----------------------------------------------------
# Helper functions

# For load
def to_array(s: str) -> list:
    s = s.replace(r'{', '')
    s = s.replace(r'}', '')
    s = s.replace(r' ', '')    

    if s == '': return []

    # return list(map(int,s.split(',')))
    return s.split(',')


# For save
def to_string(s: list) -> str:
    if len(s) == 0: 
        row = r"{}"
    else: 
        row = r"{" + " ,".join(s) + r"}"
    return row


def load(csv_path: str) -> dict:
    original = {}
    original_df = pd.read_csv(csv_path)

    global TOTAL_COST_SUM
    global TOTAL_NUM_FRAGMENTS

    for i in range(len(original_df)):
        row = original_df.loc[i]

        # NOTE: Procedure is skipped in this algorithm
        tmp = []
        tmp.append(to_array(row[2]))    # producer statement	
        tmp.append(to_array(row[3]))    # consumer statement	
        tmp.append(row[4])              # cost	
        tmp.append(row[5])              # result size

        fragments = to_array(row[6])
        tmp.append(fragments)
        # tmp.append(row[0])              # Procedure
        
        original[str(row[1])] = tmp     # Statement

        TOTAL_COST_SUM += row[4]                #type:ignore
        TOTAL_NUM_FRAGMENTS += len(fragments)   #type:ignore
    return original


def save_csv(data: list, file_name: str, info_name: str, path: str, default_path: str="output") -> None:
    COLUMNS = ['Procedure', 'Statement', 'producer statement', 'consumer statement',
                'cost', 'result size', 'Fragment', "consist", "benefit"]
    
    path = os.path.join(default_path, info_name, path)
    if not os.path.exists(path):
        os.makedirs(path)
    
    with open(os.path.join(path, f"{file_name}.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

        for d in data:
            writer.writerow(d)


# -----------------------------------------------------
# Logics

def rule_A(cost: int) -> bool:
    global TOTAL_COST_SUM
    if cost > TOTAL_COST_SUM/4: return False    # type: ignore
    else: return True

def rule_B(fragments: list) -> bool:
    global TOTAL_NUM_FRAGMENTS
    if len(fragments) > TOTAL_NUM_FRAGMENTS/4: return False # type: ignore
    else: return True


def compute_total_benefit(info: dict):
    '''
    Compute total benefit of current statements.

    Used for computing {rule_A}.
    '''
    total_benefit = 0
    for statement in info:
        row = info[statement]

        if len(row) > 5:
            total_benefit += row[BENEFIT]
    
    return total_benefit


def merge(info: dict, producer_key: str, consumer_key: str) -> Tuple[None, None]|Tuple[str, list]:
    '''
    Merge producer and consumer.
    '''
    p = info[producer_key]
    c = info[consumer_key]


    # Compute part of merged info for determination
    cost = p[COST] + c[COST]
    fragments = p[FRAGMENTS] + c[FRAGMENTS]


    # Determine whether to merge using rules.
    if not(rule_A(cost) and rule_B(fragments)): return None, None


    # Compute producer_statements and consumer_statements
    '''
    NOTE: producer/consumer_statements MUST have unique statements.
    c.f. When both producer and consumer have the same statements in producer/consumer_statements list.
    
    This is done by using set().
    '''
    # Remove keys in producer statements
    producer_statements = list(set(p[PRODUCER_STATEMENTS] + c[PRODUCER_STATEMENTS]))

    producer_statements.remove(producer_key)
    if consumer_key in producer_statements:
        producer_statements.remove(consumer_key)

    if producer_statements is None: producer_statements = []

    # Remove keys in consumer statements
    consumer_statements = list(set(p[CONSUMER_STATEMENTS] + c[CONSUMER_STATEMENTS]))

    consumer_statements.remove(consumer_key)
    if producer_key in consumer_statements:
        consumer_statements.remove(producer_key)

    if consumer_statements is None: consumer_statements = []


    # Compute result_size, consist, benefit
    result_size = c[RESULT_SIZE]  #p[3] + c[3]
    consist = []
    benefit = p[RESULT_SIZE]

    # If producer statement is merged one, then inherit it.
    if len(p) > 5:  
        result_size += p[RESULT_SIZE]
        consist.extend(p[CONSIST])
        benefit += p[BENEFIT]
    else:
        consist.append(producer_key)
        

    # If consumer statement is merged one, then inherit it.
    if len(c) > 5: consist.extend(c[CONSIST])
    else: consist.append(consumer_key)

    consist = sorted(consist)   # for visual


    # Pack the result
    merge_row = [
        producer_statements,
        consumer_statements,
        cost,
        result_size,
        fragments,
        consist,
        benefit
    ]


    # Make new statement
    merge_statement = "EB-" + "-".join(map(str, list(consist)))

    return merge_statement, merge_row


def update(info: dict, merged_statements: list[str], merge_statement: str) -> None:
    '''
    Inplace function
    '''
    
    # Delete merged statements
    for merged_key in merged_statements:
        del info[merged_key]

    # Propagate update
    # i.e. Replace merged statements in other statements' producer/consumer list 
    # with merged statements
    for statement in info:
        row = info[statement]

        def search_and_delete(array: list):
            deleted = False
            for i in reversed(range(len(array))):
                if array[i] in merged_statements:
                    del array[i]
                    deleted = True
                    
                    
            if deleted: array.append(merge_statement)
        
        search_and_delete(row[PRODUCER_STATEMENTS])
        search_and_delete(row[CONSUMER_STATEMENTS])


    