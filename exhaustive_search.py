
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

# -----------------------------------------------------

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


def save(target_list: list, total_benefit: int, procedure: str, path: str="output/es") -> None:
    COLUMNS = ['Procedure', 'Statement', 'producer statement', 'consumer statement',
                'cost', 'result size', 'Fragment', "consist", "benefit"]
    
    path = os.path.join(path, str(total_benefit))
    os.makedirs(path)
    for i, category in enumerate(target_list):  
        with open(os.path.join(path, f"{i}.csv"), "w") as c:
            writer = csv.writer(c)            
            writer.writerow(COLUMNS)

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
                writer.writerow(row)




def main():
    original = load("Statement-Infomation.csv")

    search_result = {}
    search_result["next"] = []
    search(original, search_result["next"])

    result = {}
    categorically_extract_terminal_node(search_result, result)

    # Sort resulting statements info list with total_benefit in descending order
    result = dict(sorted(result.items(), reverse=True))

    best_benefit = next(iter(result))
    best_benefit_list = result[best_benefit]

    # save(best_benefit_list, best_benefit, "5")

if __name__ == "__main__":
    # main()    

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
        main()
        result = time.time() - t
        print(result)
        benchmark.append(result)

    with open("analysis/es_benchmark.txt", "w") as f:
        for b in benchmark:
            f.write(str(b))
            f.write("\n")