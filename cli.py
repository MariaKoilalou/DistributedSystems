def run_cli(node_instance, blockchain_instance, shutdown_event):
    print("\nWelcome! Use help to see the available commands.")

    while not shutdown_event.is_set():
        action = input()
        print("\n")
        if action == 'balance':
            my_balance = node_instance.check_balance()
            print(f"Balance= {my_balance}")
        elif action == 'view':
            node_instance.view()
            print(f"{node_instance.nodes}")
        elif action.startswith('t '):
            parts = action.split()
            if len(parts) == 3:
                _, recipient_address, amount = parts
                node_instance.create_transaction(recipient_address, amount)
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

        elif action == 'exit':
            print('Exiting...')
            break  # Break out of the loop to exit the CLI

        elif action == 'help':
            help_str = '''

HELP\n
Available commands:\n
1. t <recipient_address> <amount>\n
\t--New transaction: send to recipient_address wallet the amount amount of NBC coins to get from wallet sender_address. 
\t  It will call create_transaction function in the backend that will implement the above function.\n
2. view\n
\t--View last transactions: print the transactions contained in the last validated block of the blockchain.\n
3. balance\n
\t--Show balance: print the balance of the wallet.\n
4. stake <amount>\n
\t--Stake a certain amount in the blockchain network.\n
5. help\n
'''
            print(help_str)

        else:
            print('Invalid command! Retry or use help to see the available commands.')
    print("CLI shutting down...")