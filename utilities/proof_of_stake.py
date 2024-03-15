import random

class BlockChain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.stakes = {}  

    def stake(self, node_identifier, amount):
        """
        Allow nodes to stake BCC for the validation process.
        """
        self.stakes[node_identifier] = self.stakes.get(node_identifier, 0) + amount

    def validate_block(self, block):
        """
        Validate the block by selecting a validator based on their stake.
        """
        total_stakes = sum(self.stakes.values())
        if total_stakes == 0:
            return False 

        stake_target = random.uniform(0, total_stakes)
        current = 0
        for node_identifier, stake_amount in self.stakes.items():
            current += stake_amount
            if current >= stake_target:
                validator = node_identifier
                break

        print(f"Validator selected: {validator}")

        # here we need to call the mint for this validator
        
        self.chain.append(block)
        return True
