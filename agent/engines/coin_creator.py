import os
import json
import time
import hashlib
import requests
from web3 import Web3
from engines.prompts import get_coin_creation_prompt

# Zora Factory contract on Base
ZORA_FACTORY_ADDRESS = "0x777777751622c0d3258f214F9DF38E35BF45baF3"
ZORA_API_BASE_URL = "https://api-sdk.zora.engineering/api"
BASE_CHAIN_ID = 8453
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Minimal ABI for the ZoraFactory deploy function and CoinCreatedV4 event
ZORA_FACTORY_ABI = [
    {
        "inputs": [
            {"name": "payoutRecipient", "type": "address"},
            {"name": "owners", "type": "address[]"},
            {"name": "uri", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "symbol", "type": "string"},
            {"name": "poolConfig", "type": "bytes"},
            {"name": "platformReferrer", "type": "address"},
            {"name": "postDeployHook", "type": "address"},
            {"name": "postDeployHookData", "type": "bytes"},
            {"name": "coinSalt", "type": "bytes32"},
        ],
        "name": "deploy",
        "outputs": [
            {"name": "coin", "type": "address"},
            {"name": "postDeployHookDataOut", "type": "bytes"},
        ],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "msgSender", "type": "address"},
            {"name": "name", "type": "string"},
            {"name": "symbol", "type": "string"},
            {"name": "poolConfig", "type": "bytes"},
            {"name": "platformReferrer", "type": "address"},
            {"name": "coinSalt", "type": "bytes32"},
        ],
        "name": "coinAddress",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "caller", "type": "address"},
            {"indexed": True, "name": "payoutRecipient", "type": "address"},
            {"indexed": True, "name": "platformReferrer", "type": "address"},
            {"indexed": False, "name": "currency", "type": "address"},
            {"indexed": False, "name": "uri", "type": "string"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": False, "name": "symbol", "type": "string"},
            {"indexed": False, "name": "coin", "type": "address"},
        ],
        "name": "CoinCreatedV4",
        "type": "event",
    },
]


def get_pool_config(creator_address, currency_type="ETH", zora_api_key=None):
    """
    Fetch pool configuration from the Zora API.

    Parameters:
    - creator_address (str): The creator's wallet address.
    - currency_type (str): One of ETH, ZORA, CREATOR_COIN, CREATOR_COIN_OR_ZORA.
    - zora_api_key (str): Optional Zora API key to avoid rate limiting.

    Returns:
    - bytes: The encoded pool config bytes for the deploy() call.
    """
    headers = {"Content-Type": "application/json"}
    if zora_api_key:
        headers["api-key"] = zora_api_key

    params = {
        "creatorIdentifier": creator_address,
        "currencyType": currency_type,
    }

    response = requests.get(
        f"{ZORA_API_BASE_URL}/contentCoinPoolConfig",
        params=params,
        headers=headers,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get pool config from Zora API: {response.text}")

    data = response.json()
    pool_config_hex = data.get("poolConfig") or data.get("config")
    if not pool_config_hex:
        raise Exception(f"No poolConfig in Zora API response: {data}")

    if isinstance(pool_config_hex, str) and pool_config_hex.startswith("0x"):
        return bytes.fromhex(pool_config_hex[2:])

    return bytes.fromhex(pool_config_hex)


def generate_coin_salt(name, creator_address):
    """Generate a deterministic salt for coin deployment."""
    salt_input = f"{name}{creator_address}{int(time.time())}".encode()
    return Web3.keccak(salt_input)


def get_coin_address_from_receipt(w3, receipt):
    """
    Extract the deployed coin address from a transaction receipt
    by looking for the CoinCreatedV4 event.

    Parameters:
    - w3: Web3 instance.
    - receipt: Transaction receipt.

    Returns:
    - str: The deployed coin contract address, or None if not found.
    """
    factory = w3.eth.contract(
        address=Web3.to_checksum_address(ZORA_FACTORY_ADDRESS),
        abi=ZORA_FACTORY_ABI,
    )

    for log in receipt.get("logs", []):
        try:
            decoded = factory.events.CoinCreatedV4().process_log(log)
            return decoded["args"]["coin"]
        except Exception:
            continue

    return None


def create_coin(
    private_key,
    base_rpc_url,
    name,
    symbol,
    metadata_uri,
    payout_recipient=None,
    owners=None,
    currency_type="ETH",
    platform_referrer=None,
    zora_api_key=None,
):
    """
    Create a new coin on the Zora protocol via Base chain.

    Parameters:
    - private_key (str): The private key of the creator's wallet.
    - base_rpc_url (str): Base chain RPC URL.
    - name (str): Coin name (e.g., "My Awesome Coin").
    - symbol (str): Ticker symbol (e.g., "MAC").
    - metadata_uri (str): URI pointing to coin metadata (e.g., IPFS URI).
    - payout_recipient (str): Address to receive creator rewards. Defaults to creator.
    - owners (list): List of owner addresses. Defaults to [creator].
    - currency_type (str): ETH, ZORA, CREATOR_COIN, or CREATOR_COIN_OR_ZORA.
    - platform_referrer (str): Optional referral address.
    - zora_api_key (str): Optional Zora API key.

    Returns:
    - dict: {tx_hash, coin_address} on success.
    - str: Error message on failure.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(base_rpc_url))

        if not w3.is_connected():
            return "Failed to connect to Base chain"

        account = w3.eth.account.from_key(private_key)
        creator_address = account.address

        if not payout_recipient:
            payout_recipient = creator_address
        if not owners:
            owners = [creator_address]
        if not platform_referrer:
            platform_referrer = ZERO_ADDRESS

        payout_recipient = Web3.to_checksum_address(payout_recipient)
        owners = [Web3.to_checksum_address(addr) for addr in owners]
        platform_referrer = Web3.to_checksum_address(platform_referrer)

        # Fetch pool config from Zora API
        print(f"Fetching pool config for {currency_type} coin...")
        pool_config = get_pool_config(creator_address, currency_type, zora_api_key)

        # Generate deterministic salt
        coin_salt = generate_coin_salt(name, creator_address)

        # Build contract interaction
        factory = w3.eth.contract(
            address=Web3.to_checksum_address(ZORA_FACTORY_ADDRESS),
            abi=ZORA_FACTORY_ABI,
        )

        # Build the deploy transaction
        tx = factory.functions.deploy(
            payout_recipient,
            owners,
            metadata_uri,
            name,
            symbol,
            pool_config,
            platform_referrer,
            Web3.to_checksum_address(ZERO_ADDRESS),  # postDeployHook
            b"",  # postDeployHookData
            coin_salt,
        ).build_transaction(
            {
                "from": creator_address,
                "value": 0,  # No ETH needed for coin creation itself
                "nonce": w3.eth.get_transaction_count(creator_address),
                "gasPrice": int(w3.eth.gas_price * 1.1),
                "chainId": BASE_CHAIN_ID,
            }
        )

        # Estimate gas
        try:
            gas_estimate = w3.eth.estimate_gas(tx)
            tx["gas"] = int(gas_estimate * 1.2)  # 20% buffer
        except Exception as e:
            print(f"Gas estimation failed, using fallback: {e}")
            tx["gas"] = 500000

        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"Coin creation tx sent: {tx_hash.hex()}")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt["status"] != 1:
            return f"Coin creation transaction failed (tx: {tx_hash.hex()})"

        # Extract coin address from logs
        coin_address = get_coin_address_from_receipt(w3, receipt)

        result = {
            "tx_hash": tx_hash.hex(),
            "coin_address": coin_address,
        }

        print(f"Coin created successfully!")
        print(f"  Transaction: {tx_hash.hex()}")
        print(f"  Coin address: {coin_address}")

        return result

    except Exception as e:
        return f"Error creating coin: {e}"


def coin_creation_decision(posts, short_term_memory, llm_api_key):
    """
    Use LLM to decide whether to create a coin and with what parameters.

    Parameters:
    - posts (list): Recent posts/context.
    - short_term_memory (str): Current short-term memory context.
    - llm_api_key (str): Hyperbolic API key.

    Returns:
    - dict or None: {name, symbol, description} if creating, None otherwise.
    """
    prompt = get_coin_creation_prompt(posts, short_term_memory)

    response = requests.post(
        url="https://api.hyperbolic.xyz/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_api_key}",
        },
        json={
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": "Respond only with the JSON object for coin creation or an empty object.",
                },
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "presence_penalty": 0,
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 40,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Error getting coin creation decision: {response.text}")

    content = response.json()["choices"][0]["message"]["content"]
    print(f"Coin creation decision: {content}")
    return content
