import { defineConfig } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

export default defineConfig({
  plugins: [hardhatEthers],
  solidity: {
    version: "0.8.28",
    settings: {
      evmVersion: "berlin",
    },
  },
  networks: {
    hardhat: {
      type: "edr-simulated",
      chainId: 1,
    },
  },
});
