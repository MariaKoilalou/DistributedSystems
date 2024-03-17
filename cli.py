import sys
import signal
import requests
import json
from flask import jsonify
import node
import wallet
import blockchain 

# Example setup - replace these with your actual data retrieval or configuration logic
host = "127.0.0.1"
port = 8080
blockchain = blockchain.Blockchain()  # This should be your blockchain instance or configuration
my_wallet = wallet.Wallet()  # Assuming you have a Wallet class and this is how you instantiate it

# Now, initialize your Node with these parameters
node_instance = node.Node(host, port, blockchain, my_wallet)


# case of asynchronous termination
def signal_handler(sig, frame):
    print("Forced Termination")
    # exiting python, 0 means "successful termination"
    sys.exit(0)

print("")
print("Welcome! Use help to see the available commands.")


while (1):
    action = input()
    print("\n")
    if(action == 'balance'):
        my_wallet.show_balance()
    elif(action == 'view'):
        node_instance.view()
    elif action.startswith('t '):
        parts = action.split()
        if len(parts) == 3:
            _, recipient_address, amount = parts
            node_instance.sendTransCli(recipient_address, amount)
        else:
            print("Invalid command format. Expected: 't <recipient_address> <amount>'")

    elif action.startswith('stake '):
        parts = action.split()
        if len(parts) == 2:
            _, amount_str = parts
            try:
                amount = float(amount_str)
                node_instance.stake(amount)
            except ValueError:
                print("Invalid amount. Please enter a numeric value.")
            except Exception as e:
                print(f"Error staking: {e}")
        else:
            print("Invalid command format. Expected: 'stake <amount>'")

    elif(action == 'exit'):
        print('Exiting...')
        sys.exit(0)
    
    elif(action == 'help'):
        help_str='''
HELP\n
Available commands:\n
1. t <recipient_address> <amount> \n
\t--New transaction: send to recipient_address wallet the amount amount of NBC coins to get from wallet sender_address. 
\t  It will call create_transaction function in the backend that will implements the above function.\n
2. view\n
\t--View last transactions: print the transactions contained in the last validated block of noobcash blockchain.\n
3. balance\n
\t--Show balance: print the balance of the wallet.\n
4. stake <amount> \n
\t--Stake a certain amount in the blockchain network. \n
5. help\n
'''
        print(help_str)

    else:
        print('Invalid command! Retry or use help to see the available commands')