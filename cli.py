import os


def run_cli(node_instance, shutdown_event):
    print("\nWelcome! Use help to see the available commands.")

    while not shutdown_event.is_set():
        action = input()
        print("\n")
        if action.startswith('start test'):
                # Automatically select the transactions folder based on total_nodes
                transactions_folder = ''
                if node_instance.total_nodes == 5:
                    transactions_folder = '5_nodes'
                elif node_instance.total_nodes == 10:
                    transactions_folder = '10_nodes'
                else:
                    print("Unsupported number of total nodes. Exiting...")
                    return
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # Construct the path to the transactions folder relative to the script directory
                transactions_folder_path = os.path.join(script_dir, transactions_folder)
                
                # Verify the existence of the transactions folder
                if not os.path.exists(transactions_folder_path):
                    print(f"The transactions folder '{transactions_folder}' does not exist in the current directory.")
                    return

                node_addresses = [node_info["address"] for node_id, node_info in node_instance.nodes.items()]
                node_instance.start_test_all_nodes(node_addresses, transactions_folder)
                print(f"Started transaction test for all nodes using transactions from '{transactions_folder}' folder.")

        if action == 'take metrics':
            node_instance.take_metrics()

        if action == 'balance':
            my_balance = node_instance.calculate_balance(node_instance.wallet.public_key)
            my_stakes = node_instance.calculate_stakes(node_instance.wallet.public_key)

            print(f"Balance= {my_balance}")
            print(f"Staked amount= {my_stakes}")

        elif action == 'view':
            node_instance.view()
            print(f"{node_instance.nodes}")
        elif action.startswith('t '):
            parts = action.split(' ', 2)  # Split the action into parts, but limit to 3 parts
            if len(parts) >= 3:
                _, recipient_address, content = parts
                try:
                    # Try to convert the content to a float, assuming it's an amount for a coin transfer
                    amount = float(content)
                    # Call the create_transaction method for transferring coins
                    if node_instance.create_transaction(recipient_address, amount, message="", type_of_transaction="coin"):
                        print(f"Transferred {amount} BCC to {recipient_address}.")
                    else:
                        print(f"Transferred failed.")
                except ValueError:
                    # If conversion fails, treat the content as a message
                    message = content
                    message_cost = 0  
                    # Call the create_transaction method for sending a message
                    if node_instance.create_transaction(recipient_address, message_cost, message, type_of_transaction="message"):
                        print(f"Sent message to {recipient_address}")
                    else:
                        print("Transferred failed.")

            else:
                print("Invalid command format. Expected: 't <recipient_address> <amount/message>'")
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
5. start_test <transactions_folder>\n
\t--Start transaction test: process transactions from the specified folder (e.g., '5_nodes').\n
6. help\n
'''
            print(help_str)

        else:
            print('Invalid command! Retry or use help to see the available commands.')
    print("CLI shutting down...")