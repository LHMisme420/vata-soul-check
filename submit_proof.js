const { ethers } = require("ethers");

async function main() {
  const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
  const contract = new ethers.Contract(
    "0x966118502E953a517f805807266e1275d61861FE",
    ["function verifyProof(uint[2] calldata _pA, uint[2][2] calldata _pB, uint[2] calldata _pC, uint[1] calldata _pubSignals) public view returns (bool)"],
    wallet
  );

  const pA = ["0x0e3b43533f5f62ec9e890081b4fe3d15ec14e17afa04d9266c453fecf4e71ecd","0x0456fb3cb8b479a873ec1d12797c5d3447f4714e4ccda85351e9651b93358593"];
  const pB = [["0x0cf4400100bcf5bb7f1065b5452e91f605867cd248d8633f61fa96034ae15002","0x110359e15003ea4f41eac538db1f57c65b479ba1ef9cbaf4980e2cc75fac7f4b"],["0x20e5ea3ff3f7e30788102157376240c88083eb0ccf9cdd4d3f93b3349671c87b","0x0d0fbf86ce1a540163f2629d115f995bdea3b2daeedd96a567e091ddb669116c"]];
  const pC = ["0x194ff445d49b7809f51c57950a0f15a510720d64dcdfcf8d3eb959eec63c8d07","0x047263b1bc510fb5f58136087920d38b0a487422945f4d4c2c45f01208d6a2cc"];
  const pubSignals = ["0x26a1de257db43f20272cd298fb3dd63fff9863282a459768d23b69e7a66c5bc4"];

  const result = await contract.verifyProof(pA, pB, pC, pubSignals);
  console.log("Proof valid:", result);
}

main().catch(console.error);
