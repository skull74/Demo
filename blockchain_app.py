import hashlib
import json
import time
from flask import Flask, jsonify, request, render_template

class Block:
    def __init__(self, index, transactions, timestamp, proof, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.proof = proof
        self.previous_hash = previous_hash

    def to_dict(self):
        return {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'proof': self.proof,
            'previous_hash': self.previous_hash
        }

    def compute_hash(self):
        block_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 4

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), 0, "0")
        genesis_block.proof = self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_new_transaction(self, sender, receiver, amount):
        transaction = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'timestamp': time.time()
        }
        self.unconfirmed_transactions.append(transaction)
        return self.last_block.index + 1

    def proof_of_work(self, block):
        block.proof = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.proof += 1
            computed_hash = block.compute_hash()
        return block.proof

    def add_block(self, block, proof):
        previous_hash = self.last_block.compute_hash()
        if previous_hash != block.previous_hash:
            return False
        if not self.is_valid_proof(block, proof):
            return False
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, proof):
        block.proof = proof
        return block.compute_hash().startswith('0' * Blockchain.difficulty)

    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        last_block = self.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.time(),
            proof=0,
            previous_hash=last_block.compute_hash()
        )
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.to_dict()

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ['sender', 'receiver', 'amount']
    if not all(k in data for k in required):
        return "Missing transaction information", 400
    index = blockchain.add_new_transaction(data['sender'], data['receiver'], data['amount'])
    return jsonify({'message': f'Transaction will be added to Block {index}'}), 201

@app.route('/mine', methods=['GET'])
def mine_block():
    block = blockchain.mine()
    if not block:
        return jsonify({'message': 'No transactions to mine'}), 200
    return jsonify({'message': 'New Block Forged', 'block': block}), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = [block.to_dict() for block in blockchain.chain]
    return jsonify({'chain': chain_data, 'length': len(chain_data)}), 200

@app.route('/simulate/transaction', methods=['POST'])
def simulate_transaction():
    data = request.get_json()
    required = ['type', 'sender', 'receiver', 'amount']
    if not all(k in data for k in required):
        return "Missing transaction details", 400
    if data['type'] not in ['supply_chain', 'finance']:
        return "Invalid transaction type", 400
    blockchain.add_new_transaction(data['sender'], data['receiver'], data['amount'])
    block = blockchain.mine()
    return jsonify({'message': f"{data['type'].capitalize()} transaction processed.", 'block': block}), 201

if __name__ == '__main__':
    app.run(port=5000, debug=True)
