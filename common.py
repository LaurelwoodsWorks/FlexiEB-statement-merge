"""
NOTE: Due to arbitrary format of statement_info and fragment_info,
it is user's responsibility to match up the format. 

Format (Columns) of statement_info:
    Procedure
    Statement
    Procedure statement
    Consumer statement
    Cost
    Total data size
    Fragments

For fragment_info,
manually specify the index of the columns required. 

"""

import pandas as pd
from typing import Tuple, Final
import os
import csv

"""
NOTE: To ease porting into c++, 
use list instead of datatypes (e.g. namedtuple)
"""

# Row Indices
PRODUCER_STATEMENTS: Final[int] = 0
CONSUMER_STATEMENTS: Final[int] = 1
COST: Final[int] = 2
TOTAL_DATA_SIZE: Final[int] = 3
FRAGMENTS: Final[int] = 4
CONSIST: Final[int] = 5
BENEFIT: Final[int] = 6



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


def load_data(path: str) -> pd.DataFrame:
    # Simple data loader

    if path[-5:] == ".xlsx":
        data = pd.read_excel(path)
    elif path[-4:] == ".csv":
        data = pd.read_csv(path)
    else:
        raise Exception("Data file must be either xlsx or csv.")
    
    return data


def preprocess_statements_info(raw_statements_info: pd.DataFrame, fragments_info: dict)->list:
    """
    Preprocess statements information 
    and split by procedures.

    Output: (Tuple) (procedure index, procedure) 

    NOTE: Procedures and Statements are treated as string
    because they are used in formatting (e.g. EB-2-4-7).
    """

    procedures = []
    current_procedure_index = None
    current_procedure = {}
    for row in raw_statements_info.values.tolist():
        # Initialize
        if current_procedure_index is None:
            current_procedure_index = row[0]
        
        # Split when meeting new procedure_index
        if len(current_procedure) > 0 and current_procedure_index != row[0]:
            procedures.append((current_procedure_index, current_procedure))
            current_procedure = {}
            current_procedure_index = row[0]

        current_row = []

        current_row.append(to_array(row[2]))    # producer statements
        current_row.append(to_array(row[3]))    # consumer statements
        current_row.append(float(row[4]))     # cost
        current_row.append(int(row[5]))     # total data size
        
        fragments = to_array(row[6])
        current_row.append(fragments)    # fragments

        # Compute fragments size
        fragment_size = 0
        for fragment in fragments:
            fragment_size += fragments_info[fragment]
        current_row.append(fragment_size)

        current_procedure[str(row[1])] = current_row
    
    return procedures


def preprocess_fragments_info(raw_fragments_info: pd.DataFrame, 
                              fragment_col_index: int, 
                              size_col_index: int) -> dict:
    """
    Preprocess statement information 
    and split by procedures.
    """

    fragments = {}
    for row in raw_fragments_info.values.tolist():
        fragments[str(row[fragment_col_index])] = int(row[size_col_index])

    return fragments


def load(statement_path: str, 
         fragment_path: str,
         fragment_col_index: int,
         size_col_index: int,
         path_prefix="input/") -> Tuple[list, dict]:
    raw_statements_info = load_data(path_prefix + statement_path)
    raw_fragments_info = load_data(path_prefix + fragment_path)

    fragments_info = preprocess_fragments_info(raw_fragments_info, fragment_col_index, size_col_index)
    procedures_list = preprocess_statements_info(raw_statements_info, fragments_info)

    return procedures_list, fragments_info


def serialize(procedure: dict, procedure_index: str) -> list:
    print(procedure)
    serialized_procedure = [] 
    for statement, row in procedure.items():
        
        producer_statement = to_string(row[PRODUCER_STATEMENTS])
        consumer_statement = to_string(row[CONSUMER_STATEMENTS])
        cost = row[COST]
        total_data_size = row[TOTAL_DATA_SIZE]
        fragments = to_string(row[FRAGMENTS])

        if len(row) > 6:
            consist = to_string(row[CONSIST])
            benefit = row[BENEFIT]
        else:
            consist = None
            benefit = None

        result_row = [
            procedure_index,
            statement,
            producer_statement,
            consumer_statement,
            cost,
            total_data_size,
            fragments,
            consist,
            benefit
        ]
        serialized_procedure.append(result_row)

    return serialized_procedure


def save(serialized_procedure: list, procedure_name: str, file_name: str, path="output"):
    COLUMNS = ['Procedure', 'Statement', 'producer statement', 'consumer statement',
            'cost', 'result size', 'Fragment', "consist", "benefit"]
    
    if procedure_name[-5:] == ".xlsx":
        name = procedure_name[:-5]
    else: # == ".csv"
        name = procedure_name[:-4]

    path = os.path.join(path, name)
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, file_name + ".csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

        for s in serialized_procedure:
            writer.writerow(s)


if __name__ == '__main__':
    STATEMENT_INFO_PATH = "input/Experiment1.xlsx"
    FRAGMENTS_INFO_PATH = "input/Fragment Information.xlsx"

    print(load(STATEMENT_INFO_PATH, FRAGMENTS_INFO_PATH, 0, 6))