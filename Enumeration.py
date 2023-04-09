from slither.slither import Slither  
from typing import List, Dict, Set
from eth_utils import to_hex
from web3 import Web3
import subprocess
import argparse
import requests
import json
import time 
import os
import re

"""Example run command: python main.py --provider-url https://eth-goerli.g.alchemy.com/v2/API-KEY --etherscan-api-key API-KEY --network goerli --eth-address 0x0xxxxxx"""


class EnumEtheruem:
    def __init__(self, provider_url: str, api_key: str, network: str):
        if not provider_url or not api_key:
            raise ValueError("Provider URL and API key must be provided.")
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.etherscan_api_key = api_key
        self.network = network

    def rate_limit(self):
        """
        Addresses 5 call per second Etherscan rate limit.
        """
        time.sleep(0.2)

    def format_output(self, title, data):
          formatted_data = json.dumps(str(data), indent=2)
          return f"{title}: {formatted_data}\n"

    def format_transaction_details(self, transaction_dict: dict) -> str:
        # Convert HexBytes values to their hexadecimal string representation
        for key, value in transaction_dict.items():
            if str(value).startswith('HexBytes'):
                transaction_dict[key] = to_hex(value)
    
        # Format the output
        formatted_output = "\n".join([f"{key}: {value}" for key, value in transaction_dict.items()])
        return formatted_output

    def extract_solidity_version(source_code: str) -> str:
        match = re.search(r"pragma solidity (\^?)([0-9]+\.[0-9]+\.[0-9]+);", source_code)
        return match.group(2) if match else None

    def setup_and_run_slither(self, file_path: str = 'file.sol'):
        solc_version = extract_solidity_version()
        # Install solc version
        subprocess.run(['solc-select', 'install', solc_version])
        
        # Use solc version
        subprocess.run(['solc-select', 'use', solc_version])
        os.environ['SOLC_VERSION'] = solc_version
        slither = Slither(file_path)
        return slither

    def basic_solidity_formatter(self, contract_sources: Dict[str, Dict]) -> Dict[str, str]:
        def format_source(source_code: str, indent_size: int = 4) -> str:
            formatted_code = []
            indent_level = 0
            for line in source_code.split('\n'):
                stripped_line = line.strip()
    
                if stripped_line.startswith('}'):
                    indent_level -= 1
    
                formatted_line = ' ' * (indent_size * indent_level) + stripped_line
                formatted_code.append(formatted_line)
    
                if stripped_line.endswith('{'):
                    indent_level += 1
    
            return '\n'.join(formatted_code)
    
        formatted_sources = {}
        for contract_address, contract_data in contract_sources.items():
            source_code = contract_data["SourceCode"]
            formatted_sources[contract_address] = {
                "SourceCode": format_source(source_code),
            }
    
        return formatted_sources

      
    def get_eth_balance(self, eth_address: str) -> float:
        """
        Returns the balance of an Ethereum address in Ether.
        """
        if not Web3.is_address(eth_address):
            raise ValueError("Invalid Ethereum address.")
        
        balance = self.w3.eth.get_balance(eth_address)
        balance_in_ether = self.w3.from_wei(balance, "ether")
        return balance_in_ether
      

    def get_transaction_count(self, address: str) -> int:
        if not Web3.is_address(address):
            raise ValueError("Invalid Ethereum address.")
        
        transaction_count = self.w3.eth.get_transaction_count(address)

        return transaction_count


    def get_transactions_details(self, tx_hashes: List[str]) -> Dict[str, Dict]:
        """
        Returns a dictionary with details of the transactions for the given transaction hashes.
    
        Args:
            tx_hashes (List[str]): A list of transaction hashes to query.
    
        Returns:
            transactions_details (Dict[str, Dict]): A dictionary mapping transaction hashes to their corresponding transaction details.
        """
        transactions_details = {}
        for tx_hash in tx_hashes:
            transaction = self.w3.eth.get_transaction(tx_hash)
            transaction_details = dict(transaction)
            transactions_details[tx_hash] = transaction_details
    
        return transactions_details


    def get_tx_hashes(self, address: str) -> List[str]:
        if not Web3.is_address(address):
            raise ValueError("Invalid Ethereum address.")
        
        if self.network == "mainnet":
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        elif self.network == "goerli":
            url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        else:
            raise ValueError("Invalid network. Must be 'mainnet' or 'goerli'.")

        self.rate_limit()
      
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching data from Etherscan API: {str(e)}")
    
        if response.status_code == 200:
            data = response.json()
            if data['status'] == "1":
                tx_hashes = [tx['hash'] for tx in data['result']]
                return tx_hashes
            elif data['status'] == "0" and data['message'] == "No transactions found":
                raise ValueError(f"No transactions found for address: {address}") 
            else:
                raise ValueError(f"Etherscan API error: {data['message']}")
        else:
            raise ValueError("Error fetching data from Etherscan API")


    def get_contract_addresses(self, address: str) -> List[str]:
        if not Web3.is_address(address):
            raise ValueError("Invalid Ethereum address.")
        
        if self.network == "mainnet":
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        elif self.network == "goerli":
            url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={self.etherscan_api_key}"
        else:
            raise ValueError("Invalid network. Must be 'mainnet' or 'goerli'.")

        self.rate_limit()
      
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching data from Etherscan API: {str(e)}")

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

    def get_erc20_token_balance(self, contract_address, contract_abi, eth_address):
        if not Web3.is_address(contract_address) or not Web3.is_address(eth_address):
            raise ValueError("Invalid Ethereum address.")
        
        contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
        try:
            token_balance = contract.functions.balanceOf(eth_address).call()
        except Exception as e:
            raise ValueError(f"Error calling balanceOf function: {str(e)}")
        return token_balance
      

    def get_contract_codes(self, contract_addresses: List[str]) -> Dict[str, str]:
        """
        Gets the contract codes at the specified Ethereum addresses.
    
        Args:
            contract_addresses (List[str]): A list of Ethereum addresses to query.
    
        Returns:
            codes (Dict[str, str]): A dictionary mapping Ethereum addresses to their corresponding contract codes.
        """
        codes = {}
        for address in contract_addresses:
            if not Web3.is_address(address):
                raise ValueError(f"Invalid Ethereum address: {address}")
            
            code = self.w3.eth.get_code(address)
            codes[address] = code.hex()
    
        return codes
    
    
    def get_contracts_abis(self, contract_addresses: List[str]) -> Dict[str, Dict]:
        """
        Gets the ABIs of the specified Ethereum contract addresses.
    
        Args:
            contract_addresses (List[str]): A list of Ethereum addresses to query.
    
        Returns:
            abis (Dict[str, Dict]): A dictionary mapping Ethereum addresses to their corresponding contract ABIs.
        """
        abis = {}
        for contract_address in contract_addresses:
            if not Web3.is_address(contract_address):
                raise ValueError(f"Invalid Ethereum address: {contract_address}")
            
            url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={self.etherscan_api_key}"

            self.rate_limit()
          
            try:
                response = requests.get(url)
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Error fetching data from Etherscan API: {str(e)}")
    
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    abi = data['result']
                    abis[contract_address] = abi
                else:
                    raise ValueError(f"Failed to retrieve ABI for contract address {contract_address}. Error message: {data['message']}")
            else:
                raise ValueError(f"Failed to retrieve ABI for contract address {contract_address}. HTTP status code: {response.status_code}")
    
        return abis


    def get_contract_source_codes(self, contract_addresses) -> Dict[str, Dict]:
        """
        Gets the Solidity code for an Ethereum contract at the specified address.
        
        Args:
            contract_address (str): The Ethereum address of the contract to query.
            api_key (str): Your Etherscan API key.
        
        Returns:
            source_code (str): The Solidity code of the contract.
        """
        contract_source_codes = {}
        for contract_address in contract_addresses:
            if not Web3.is_address(contract_address):
                raise ValueError(f"Invalid Ethereum address: {contract_address}")
            
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={self.etherscan_api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    source_code = data['result'][0]
                    contract_source_codes[contract_address] = source_code
                else:
                    raise ValueError(f"Failed to retrieve contract source code for address {contract_address}. Error message: {data['message']}")
            else:
                raise ValueError(f"Failed to retrieve contract source code for address {contract_address}. HTTP status code: {response.status_code}")
              
        return contract_source_codes

    def get_contract_info(self, contract_abis):
        contract_info = {}
        for contract_address, contract_abi in contract_abis.items():
            print(contract_address)
            print(contract_abi)
            if not self.w3.is_address(contract_address):
                raise ValueError("Invalid Ethereum address.")
            
            contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            
            try:
                token_name = contract.functions.name().call()
                token_symbol = contract.functions.symbol().call()
                token_decimals = contract.functions.decimals().call()
            except Exception as e:
                raise ValueError(f"Error getting contract info for address {contract_address}: {str(e)}")
            
            contract_info[contract_address] = {
                "name": token_name,
                "symbol": token_symbol,
                "decimals": token_decimals
            }
    
        return contract_info



def enumerate_ethereum():
    parser = argparse.ArgumentParser(description='Enumerate Ethereum account')
    parser.add_argument('--provider-url', type=str, help='URL of the Ethereum node provider')
    parser.add_argument('--etherscan-api-key', type=str, help='API key for Etherscan API')
    parser.add_argument('--eth-address', type=str, help='Ethereum address (Optional: You will need to provide a contract-address if you dont provide an eth-address)')
    parser.add_argument('--contract-address', type=str, help='Contract address (Optional: You will need to provide an eth-address if you dont provide a contract-address)')
    parser.add_argument('--network', type=str, help='Ethereum network (mainnet or goerli)')

    args = parser.parse_args()

    if not args.eth_address and not args.contract_address:
        parser.error("At least one of --eth-address or --contract-address must be provided.")

    try:
        enum_ethereum = EnumEtheruem(args.provider_url, args.etherscan_api_key, args.network)
        if args.eth_address:
            eth_balance = enum_ethereum.get_eth_balance(args.eth_address)
            tx_hashes = enum_ethereum.get_tx_hashes(args.eth_address)
            transaction_count = enum_ethereum.get_transaction_count(args.eth_address)
            contract_addresses = enum_ethereum.get_contract_addresses(args.eth_address)
            transaction_details = enum_ethereum.get_transactions_details(tx_hashes)

            print(enum_ethereum.format_output("ETH Balance", eth_balance))
            print(enum_ethereum.format_output("Transaction Count", transaction_count))
            print(enum_ethereum.format_output("Transaction Hashes", tx_hashes))
            for tx_hash, tx_detail in transaction_details.items():
              details = enum_ethereum.format_transaction_details(tx_detail)
              print(details)
            print(enum_ethereum.format_output("Contract Addresses", contract_addresses))
        
        if contract_addresses:
            contract_codes = enum_ethereum.get_contract_codes(contract_addresses)
            get_contract_source_codes = enum_ethereum.get_contract_source_codes(contract_addresses)
            # get_contract_info = enum_ethereum.get_contract_info(get_contracts_abis)
            print(enum_ethereum.format_output("Contract Code", contract_codes))
            # print(get_contract_source_codes)
            print(enum_ethereum.basic_solidity_formatter(get_contract_source_codes))
            
          
        if args.contract_address:
            contract_codes = enum_ethereum.get_contract_code(args.contract_address)
            print(enum_ethereum.format_output("Contract Code", contract_codes))

    except ValueError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    enumerate_ethereum()
