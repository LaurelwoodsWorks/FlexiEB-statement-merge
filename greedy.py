import pandas as pd
from copy import deepcopy

from common import *


class Greedy:
    def __init__(self, statements, fragments_info, procedure_index, num_ERN=4, rule_A_weight=1., rule_B_weight=1.):
        self.statements = statements
        self.fragments_info = fragments_info
        self.procedure_index = procedure_index
        self.num_ERN = num_ERN
        self.rule_A_weight = rule_A_weight
        self.rule_B_weight = rule_B_weight

        self.total_cost, self.total_fragments_size = self.initialize_constants()

    
    def initialize_constants(self) -> Tuple[int, int]:
        """
        Initialize constants for rules
        """

        total_cost = 0
        total_fragments_size = 0

        for _, row in self.statements.items():
            total_cost += row[COST]

            for fragment in row[FRAGMENTS]:
                total_fragments_size += self.fragments_info[fragment]
        
        return total_cost, total_fragments_size


    def is_merged(self, statement_info) -> bool:
        return len(statement_info) > CONSIST + 1


    def rule_A(self, cost: float) -> bool:
        if cost > self.total_cost / self.num_ERN * self.rule_A_weight: return False
        else: return True

    
    def rule_B(self, fragment_size: int) -> bool:
        if fragment_size > self.total_fragments_size / self.num_ERN * self.rule_B_weight: return False
        else: return True


    def compute_total_benefit(self):
        '''
        Compute total benefit of current statements.

        Used for computing {rule_A}.
        '''

        total_benefit = 0
        for statement in self.statements:
            row = self.statements[statement]

            if self.is_merged(row):
                total_benefit += row[BENEFIT]
        
        return total_benefit


    def get_candidate_list(self, statements) -> list:
        """
        Get candidates for greedy algorithm
        """

        # Sort candidate statements by expected benefits in descending order
        candidates_list = []
        for statement, row in statements.items():
            # NOTE: statement is consumer

            if len(row[CONSUMER_STATEMENTS]) > 0: 
                # If statement is merged statement, also consider existing benefit
                if self.is_merged(row):
                    expected_benefit = row[TOTAL_DATA_SIZE] + row[BENEFIT]
                else:
                    expected_benefit = row[TOTAL_DATA_SIZE]
                    
                candidates_list.append([statement, expected_benefit])
        
        # Sort candidates by expected benefits in descending order 
        candidates_list = sorted(candidates_list, key=lambda x: -x[1]) 

        return candidates_list
    


    def merge(self, statements, producer_key: str, consumer_key: str) -> Tuple[None, None]|Tuple[str, list]:
        '''
        Merge producer and consumer.
        '''
        p = statements[producer_key]
        c = statements[consumer_key]


        # Compute information required by rules
        cost = p[COST] + c[COST]
        
        fragments = list(set(p[FRAGMENTS] +  c[FRAGMENTS]))
        fragments_size = 0
        for fragment in fragments:
            fragments_size += self.fragments_info[fragment]


        # Determine whether to merge using rules.
        if not(self.rule_A(cost) and self.rule_B(fragments_size)): return None, None


        def process_related_statements(index: int, key:str, opponent_key:str)->list:
            '''
            Compute producer_statements and consumer_statements
            
            NOTE: producer/consumer_statements MUST have unique statements.
            c.f. When both producer and consumer have the same statements in producer/consumer_statements list.
            
            This is done by using set().
            '''

            related_statements = list(set(p[index] + c[index]))

            related_statements.remove(key)
            if opponent_key in related_statements:
                related_statements.remove(consumer_key)

            if related_statements is None: related_statements = []
            return related_statements

        # Remove keys in producer statements
        producer_statements = process_related_statements(PRODUCER_STATEMENTS, producer_key, consumer_key)
        consumer_statements = process_related_statements(CONSUMER_STATEMENTS, consumer_key, producer_key)


        # Compute other information
        result_size = c[TOTAL_DATA_SIZE]
        consist = []
        benefit = p[TOTAL_DATA_SIZE]


        # If producer statement is merged one, then inherit it.
        if self.is_merged(p):
            result_size += p[TOTAL_DATA_SIZE]
            consist.extend(p[CONSIST])
            benefit += p[BENEFIT]
        else:
            consist.append(producer_key)
            
        # If consumer statement is merged one, then inherit it.
        if self.is_merged(c): consist.extend(c[CONSIST])
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


    def update(self, statements: dict, merged_statements: list[str], merge_statement: str) -> dict:
        """
        Make a copy of statements and update it.

        NOTE: Merge statement is not included in this process.
        """

        updated_statements = deepcopy(statements)
        
        # Delete merged statements
        for merged_key in merged_statements:
            del updated_statements[merged_key]

        def search_and_delete(related_statements: list):
            """
            Propagate update
            i.e. Replace merged statements in other statements' producer/consumer list 
            with merged statements
            """

            deleted = False
            for i in reversed(range(len(related_statements))):
                if related_statements[i] in merged_statements:
                    del related_statements[i]
                    deleted = True                        
                    
            if deleted: related_statements.append(merge_statement)

        for _, row in updated_statements.items():                        
            search_and_delete(row[PRODUCER_STATEMENTS])
            search_and_delete(row[CONSUMER_STATEMENTS])

        return updated_statements


    def _search(self, statements):
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

        candidates_list = self.get_candidate_list(statements)
        
        updated = False
        
        # Outer loop for iterating over candidates
        for producer_statement, _ in candidates_list:
            target_row = statements[producer_statement]
            
            # Inner loop for merging
            for consumer_statement in target_row[CONSUMER_STATEMENTS]:             
                merge_statement, merge_row = self.merge(statements, producer_statement, consumer_statement)

                # When failed to satisfy the rules
                if merge_statement is None: continue

                # Update
                updated_statements = self.update(statements, [producer_statement, consumer_statement], merge_statement)
                updated_statements[merge_statement] = merge_row     # Add merge statement

                updated = True
                break
            

            if updated:
                break
        
        if updated:
            self._search(updated_statements) # type:ignore
        else: 
            # I don't know why statements is returned as None;
            # in debug console, statements is correctly shown.

            # return statements   # type:ignore     

            self.return_statements = statements
            return statements
    

    def search(self) -> dict:
        self._search(self.statements)

        return self.return_statements


def main(statement_info, fragments_info):
    procedures_list, fragments_info = load(statement_info, fragments_info, 0, 6)

    result = []
    for procedure_index, procedure in procedures_list:
        greedy = Greedy(procedure, fragments_info, procedure_index)
        r = greedy.search()
        result.extend(serialize(r, procedure_index))

    save(result, statement_info, "Procedure", "output/test")


# Custom
# ----------------------------------------------------------------

def test_1(statement_info, fragments_info):
    procedures_list, fragments_info = load(statement_info, fragments_info, 0, 6)

    for w in range(8):
        weight = 1.5 + w*0.5
        
        result = []
        for procedure_index, procedure in procedures_list:
            greedy = Greedy(procedure, fragments_info, procedure_index, rule_A_weight=weight)
            r = greedy.search()
            result.extend(serialize(r, procedure_index))

        save(result, statement_info, f"Experiment1-alpha={weight}", "output/Experiment1-alpha")



if __name__ == "__main__":
    STATEMENT_INFO = "Experiment1.xlsx"
    FRAGMENTS_INFO = "Fragment Information.xlsx"
    
    # main(STATEMENT_INFO, FRAGMENTS_INFO)

    test_1(STATEMENT_INFO, FRAGMENTS_INFO)

    # procedures_list, fragments_info = load(STATEMENT_INFO, FRAGMENTS_INFO, 0, 6)

    # procedure_index, procedure = procedures_list[1]
    # greedy = Greedy(procedure, fragments_info, procedure_index)
    # print(greedy.search())
