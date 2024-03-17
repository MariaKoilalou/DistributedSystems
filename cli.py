import sys
import signal
import requests
import json
from flask import jsonify
import node


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
        node.Node.balance()

    elif(action == 'view'):
        node.Node.view()
    elif(action[0] == 't'):
        inputs = action.split()
        id = inputs[1] 
        amount = inputs[2]
        node.Node.sendTransCli(id, amount)

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
4. help\n
'''
        print(help_str)

    else:
        print('Invalid command! Retry or use help to see the available commands')