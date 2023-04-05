from typing import List, Dict, Set
from web3 import Web3
from typing import Dict
import argparse
import requests
import json

class EnumEtheruem:
    def __init__(self, provider_url: str, api_key: str, network: str):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.etherscan_api_key = api_key
        self.network = network

    def get_eth_balance(self, eth_address: str) -> float:
        """
        Returns the balance of an Ethereum address in Ether.
        """
        balance = self.w3.eth.get_balance(eth_address)
        balance_in_ether = self.w3.from_wei(balance, "ether")
        return balance_in_ether

    def get_contract_code(self, address: str) -> str:
        """
        Gets the contract code at the specified Ethereum address.

        Args:
            address (str): The Ethereum address to query.

        Returns:
            str: The bytecode at the specified address.
        """
        # Get the code at the specified address
        code = self.w3.eth.get_code(address)

        return code.hex()

    def get_transaction_count(self, address: str) -> int:
        # Get the transaction count of the address
        transaction_count = self.w3.eth.get_transaction_count(address)

        return transaction_count

    def get_transaction_details(self, tx_hash: str) -> Dict:
        """
        Returns a dictionary with details of a transaction.

        Args:
        - tx_hash (str): Hash of the transaction to fetch details of

        Returns:
        - transaction_details (Dict): Dictionary with details of the transaction
        """
        # Fetch the transaction details
        transaction = self.w3.eth.get_transaction(tx_hash)

        # Convert to dictionary
        transaction_details = dict(transaction)

        return transaction_details

    def get_tx_hashes(self, address: str) -> List[str]:
        if self.network == "mainnet":
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        elif self.network == "goerli":
            url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        else:
            raise ValueError("Invalid network. Must be 'mainnet' or 'goerli'.")

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data['status'] == "1":
                tx_hashes = [tx['hash'] for tx in data['result']]
                return tx_hashes
            else:
                raise ValueError(f"Etherscan API error: {data['message']}")
        else:
            raise ValueError("Error fetching data from Etherscan API")
      

    def get_contract_addresses(self, address: str) -> List[str]:
        """
        Extracts all contract addresses from transactions of the specified address.
        """
        if self.network == "mainnet":
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        elif self.network == "goerli":
            url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        else:
            raise ValueError("Invalid network. Must be 'mainnet' or 'goerli'.")
    
        response = requests.get(url)
  
        if response.status_code == 200:
            data = response.json()
            if data['status'] == "1":
                contract_addresses = set()
                for tx in data['result']:
                    to_address = tx['to']
                    if to_address:
                        to_address = self.w3.to_checksum_address(to_address)
                        if self.w3.eth.get_code(to_address) != b'':
                            contract_addresses.add(to_address)
                return list(contract_addresses)
            else:
                raise ValueError(f"Etherscan API error: {data['message']}")
        else:
            raise ValueError("Error fetching data from Etherscan API")
        
    
    def get_erc20_token_balance(w3, contract_address, contract_abi, eth_address):
        """
        Get the balance of the address in ERC20 tokens.
        :param w3: Web3 instance
        :param contract_address: Address of the ERC20 contract
        :param contract_abi: ABI of the ERC20 contract
        :param eth_address: Address to check balance for
        :return: Balance of the address in ERC20 tokens
        """
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        token_balance = contract.functions.balanceOf(eth_address).call()
        return token_balance
    
    def get_contract_abi(contract_address):
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={self.etherscan_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                return json.loads(data['result'])
            else:
                print(f"Failed to retrieve ABI for contract address {contract_address}. Error message: {data['message']}")
        else:
            print(f"Failed to retrieve ABI for contract address {contract_address}. HTTP status code: {response.status_code}")


def enumerate_ethereum():
    parser = argparse.ArgumentParser(description='Enumerate Ethereum account')
    parser.add_argument('--provider-url', type=str, help='URL of the Ethereum node provider')
    parser.add_argument('--etherscan-api-key', type=str, help='API key for Etherscan API')
    parser.add_argument('--eth-address', type=str, help='Ethereum address(Optional: You will need to provide a contract-address if you dont provide an eth-address)')
    parser.add_argument('--contract-address', type=str, help='Contract address(Optional: You will need to provide an eth-address if you dont provide an contract-address)')
    parser.add_argument('--network', type=str, help='Ethereum network (mainnet or goerli)')

    args = parser.parse_args()

    if not args.eth_address and not args.contract_address:
        parser.error("At least one of --eth-address or --contract-address must be provided.")

    if args.eth_address:
      enum_ethereum = EnumEtheruem(args.provider_url, args.etherscan_api_key, args.network)
      eth_balance = enum_ethereum.get_eth_balance(args.eth_address)
      tx_hashes = enum_ethereum.get_tx_hashes(args.eth_address)
      transaction_count = enum_ethereum.get_transaction_count(args.eth_address)
      contract_addresses = enum_ethereum.get_contract_addresses(args.eth_address)
      transaction_details = enum_ethereum.get_transaction_details(tx_hashes[0])
      transaction_receipts = enum_ethereum.get_transaction_receipts(tx_hashes)
      # erc20_token_balance = enum_ethereum.get_erc20_token_balance(enum_ethereum.w3, args.contract_address, [], args.eth_address)
      # print("ERC20 Token Balance:", erc20_token_balance)
    if args.contract_address:
      contract_code = enum_ethereum.get_contract_code(args.contract_address)
      contract_abi = enum_ethereum.get_contract_abi(args.contract_address)
      print("Contract Code:", contract_code)
      print("Contract ABI:", contract_abi)

    print("ETH Balance:", eth_balance)
    print("Transaction Count:", transaction_count)
    print("Transaction Details:", transaction_details)
    print("Transaction Hashes:", tx_hashes)
    print("Contract Addresses:", contract_addresses)
    print("Transaction Receipts:", transaction_receipts)

if __name__ == "__main__":
    enumerate_ethereum()


