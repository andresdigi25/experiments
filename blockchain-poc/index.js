const crypto = require('crypto');

class Block {
    constructor(index, timestamp, data, previousHash = '') {
        this.index = index;
        this.timestamp = timestamp;
        this.data = data;
        this.previousHash = previousHash;
        this.hash = this.calculateHash();
    }

    calculateHash() {
        return crypto.createHash('sha256').update(this.index + this.timestamp + this.data + this.previousHash).digest('hex');
    }
}

class Blockchain {
    constructor() {
        this.chain = [this.createGenesisBlock()];
    }

    createGenesisBlock() {
        return new Block(0, new Date().toISOString(), "Genesis Block", "0");
    }

    getLatestBlock() {
        return this.chain[this.chain.length - 1];
    }

    addBlock(newBlock) {
        newBlock.previousHash = this.getLatestBlock().hash;
        newBlock.hash = newBlock.calculateHash();
        this.chain.push(newBlock);
    }

    isChainValid() {
        for (let i = 1; i < this.chain.length; i++) {
            const currentBlock = this.chain[i];
            const previousBlock = this.chain[i - 1];

            if (currentBlock.hash !== currentBlock.calculateHash()) {
                return false;
            }

            if (currentBlock.previousHash !== previousBlock.hash) {
                return false;
            }
        }
        return true;
    }
}

// Create a new blockchain
let blockchain = new Blockchain();

// Add blocks to the blockchain
blockchain.addBlock(new Block(1, new Date().toISOString(), "Transaction Data 1"));
blockchain.addBlock(new Block(2, new Date().toISOString(), "Transaction Data 2"));
blockchain.addBlock(new Block(3, new Date().toISOString(), "Transaction Data 3"));

// Print the contents of the blockchain
blockchain.chain.forEach(block => {
    console.log(`Block #${block.index}`);
    console.log(`Timestamp: ${block.timestamp}`);
    console.log(`Data: ${block.data}`);
    console.log(`Hash: ${block.hash}`);
    console.log(`Previous Hash: ${block.previousHash}`);
    console.log(`is valid? ${blockchain.isChainValid()}`);
    console.log('\n');
});