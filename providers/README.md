# Docs Provider Smart Farming

## Idea

- Smart Farming's AI agent is an AI with a continuously updated memory. By using a RAG system that updates real-time data to a non-fine-tuned memory. The RAG memory, because it is not fine-tuned, only needs to be retrieved by the AI ​​model, so the data can be continuously updated without waiting for the fine-tune time to update the model's knowledge.

- Its main knowledge is about pools information on Uniswap.

## How to work

- The latest data on Uniswap will be continuously fetched every time new blocks are generated. By using Uniswap's subgraph

- The data will then be refined and embedded and saved to the vector database - a normal database for easy retrieval.

- Every time there is a request from the adaptors, it will retrieve and query the latest data, then refine it according to the required format and respond to the requester (smart contract request).

- In addition, this AI agent also integrates auto detect modules if the data is not in the knowledge or vector database. It will call the APIs that are supported inside. In the future, auto search will be integrated.

```mermaid
sequenceDiagram
participant Uniswap Subgraph as Uniswap Subgraph
participant Data Fetcher as Data Fetcher
participant Vector Database as Vector Database
participant Adaptor as Adaptor
participant Provider as Provider (AI Agent)

    loop On New Block Generation
        Uniswap Subgraph->>Data Fetcher: Provide Latest Data
        Data Fetcher->>Data Fetcher: Refine Data
        Data Fetcher->>Vector Database: Embed and Save Data
    end

    Adaptor->>Provider: Request Latest Information
    Provider->>Vector Database: Query Latest Data
    Vector Database-->>Provider: Retrieve Refined Data
    Provider->>Adaptor: Respond with Formatted Data
```
