
import pandas as pd
import csv
from copy import deepcopy
import os
from typing import Final, Tuple


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

# ----------------------------------------------------------------

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
    producer_statements = p[PRODUCER_STATEMENTS] + c[PRODUCER_STATEMENTS]
    producer_statements.remove(producer_key)    
    if producer_statements is None: producer_statements = []

    consumer_statements = p[CONSUMER_STATEMENTS] + c[CONSUMER_STATEMENTS]
    consumer_statements.remove(consumer_key)
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
        return info



def save(target_info: dict, total_benefit: int, procedure: str, path: str="output/greedy") -> None:
    COLUMNS = ['Procedure', 'Statement', 'producer statement', 'consumer statement',
                'cost', 'result size', 'Fragment', "consist", "benefit"]
    
    os.makedirs(path)

    with open(os.path.join(path, f"{total_benefit}.csv"), "w") as c:
        writer = csv.writer(c)            
        writer.writerow(COLUMNS)

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
            writer.writerow(result_row)




def main(): 
    original = load("Statement-Infomation.csv")
    result = search(original)

    # result_ =  {
    #     '25': [[], ['EB-27-29-33', 'EB-28-30', 'EB-31-32'], 0.061239, 99090, ['88', '95', '96', '97', '101', '102', '103', '87']], 
    #     '26': [[], ['EB-27-29-33', 'EB-28-30', 'EB-31-32'], 0.045698, 73049, ['30', '24']], 
    #     '34': [['EB-27-29-33'], ['35'], 1.182939, 555294969, []], 
    #     '35': [['34'], [], 0.407706, 1, []], 
    #     'EB-27-29-33': [['25', '26', 'EB-28-30', 'EB-31-32'], ['34'], 0.47387, 569596, ['18', '17', '15', '16', '1', '4'], ['27', '29', '33'], 3069238], 
    #     'EB-28-30': [['25', '26'], ['EB-27-29-33'], 0.23311700000000002, 135789, ['150', '149', '147', '148', '125', '128'], ['28', '30'], 1441548], 
    #     'EB-31-32': [['25', '26'], ['EB-27-29-33'], 0.235688, 56139, ['186', '211', '210', '208', '209', '190'], ['31', '32'], 719384]
    # }
    # save(result_, compute_total_benefit(result_), "5")

if __name__ == "__main__":
    # main()

    import time
    t = time.time()
    main()
    result = time.time() - t
    print(result)