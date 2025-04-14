# MCP Calculator Server

<img src="http://nanda-registry.com/api/v1/verification/badge/9b41b9d1-a1e7-4144-88b8-9062e9f5a7dc/" alt="Verified Nanda Server" />
This project implements a simple calculator server using the Model Context Protocol (MCP). It provides tools for addition and multiplication, as well as a dynamic greeting resource.

## Project Structure

```
mcp-calculator-server
├── src
│   ├── calc.ts          # Main logic for the MCP calculator server
│   └── types
│       └── index.ts     # Custom types and interfaces (currently empty)
├── package.json         # npm configuration file
├── tsconfig.json        # TypeScript configuration file
└── README.md            # Project documentation
```

## Installation

To get started, clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd mcp-calculator-server
```

Then, install the required dependencies:

```bash
npm install
```

## Building the Project

To compile the TypeScript code, run:

```bash
npm run build
```

## Running the Server

To start the MCP calculator server, use the following command:

```bash
npm start
```

The server will listen for input on standard input and output the results to standard output.

## Usage

You can interact with the server by sending requests for addition, multiplication, or greetings. The server will respond with the appropriate results.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.
