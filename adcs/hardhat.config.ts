import * as dotenv from 'dotenv'
dotenv.config()

import '@typechain/hardhat'
import '@nomiclabs/hardhat-ethers'
import 'hardhat-deploy'
import '@nomiclabs/hardhat-solhint'
import '@nomicfoundation/hardhat-verify'
import '@nomicfoundation/hardhat-chai-matchers'
import '@nomicfoundation/hardhat-foundry'

module.exports = {
  typechain: {
    outDir: './typechain',
    target: 'ethers-v6'
  },
  solidity: {
    compilers: [
      {
        version: '0.8.20'
      }
    ],
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },

  networks: {
    hardhat: {
      accounts: {
        count: 10
      },
      live: false,
      saveDeployments: false
    },
    development: {
      url: 'http://127.0.0.1:8545', // Localhost (default: none)
      live: false,
      saveDeployments: true
    },
    polygon: {
      url: process.env.POLOGON_PROVIDER,
      accounts: [process.env.TESTNET_DEPLOYER],
      gasMultiplier: 1.3,
      saveDeployments: true,
      verify: {
        etherscan: {
          apiUrl: 'https://api.polygonscan.com/api',
          apiKey: process.env.EXPLORER_API_KEY
        }
      }
    },
    rivalz2_test: {
      url: 'https://rivalz2.rpc.caldera.xyz/http',
      accounts: [process.env.TESTNET_DEPLOYER],
      gasMultiplier: 1.2,
      verify: {
        etherscan: {
          apiUrl: 'https://rivalz2.explorer.caldera.xyz/api',
          apiKey: process.env.EXPLORER_API_KEY
        }
      }
    },
    arbitrum: {
      url: process.env.ARBITRUM_PROVIDER,
      accounts: [process.env.TESTNET_DEPLOYER],
      gasMultiplier: 1.2,
      verify: {
        etherscan: {
          apiUrl: 'https://api.arbiscan.io/api',
          apiKey: process.env.ARBITRUM_API_KEY
        }
      }
    },
    base: {
      url: process.env.BASE_PROVIDER,
      accounts: [process.env.TESTNET_DEPLOYER],
      gasMultiplier: 1.1,
      verify: {
        etherscan: {
          apiUrl: 'https://api.basescan.org/api',
          apiKey: process.env.BASE_API_KEY
        }
      }
    }
  },

  paths: {
    sources: './src',
    tests: './test',
    cache: './build/cache',
    artifacts: './build/artifacts',
    deployments: './deployments'
  },
  etherscan: {
    apiKey: {
      polygon: process.env.EXPLORER_API_KEY,
      rivalz2_test: process.env.EXPLORER_API_KEY,
      arbitrum: process.env.ARBITRUM_API_KEY,
      base: process.env.BASE_API_KEY
    },
    customChains: [
      {
        network: 'rivalz2_test',
        chainId: 6966,
        urls: {
          apiURL: 'https://rivalz2.explorer.caldera.xyz/api',
          browserURL: 'https://rivalz2.explorer.caldera.xyz'
        }
      },
      {
        network: 'arbitrum',
        chainId: 42161,
        urls: {
          apiURL: 'https://api.arbiscan.io/api',
          browserURL: 'https://arbiscan.io'
        }
      },
      {
        network: 'base',
        chainId: 8453,
        urls: {
          apiURL: 'https://api.basescan.org/api',
          browserURL: 'https://basescan.org'
        }
      }
    ]
  },
  namedAccounts: {
    // migrations
    deployer: {
      default: 0
    }
  }
}
