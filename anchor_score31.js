const { ethers } = require("ethers");

async function main() {
  const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  const proof = require("./proofpack/score31/proof.json");
  const pub = require("./proofpack/score31/public.json");

  const payload = JSON.stringify({ proof, pub, score: 31, epoch: 5, ts: new Date().toISOString() });
  const data = ethers.hexlify(ethers.toUtf8Bytes(payload));

  const tx = await wallet.sendTransaction({
    to: wallet.address,
    data: data,
    gasLimit: 100000
  });

  console.log("TX hash:", tx.hash);
  await tx.wait();
  console.log("Anchored in block:", (await provider.getTransactionReceipt(tx.hash)).blockNumber);
}

main().catch(console.error);
