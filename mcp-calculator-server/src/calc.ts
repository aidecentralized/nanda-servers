// filepath: /Users/tremblerz/Servers/mcp-calculator-server/src/calc.ts
import {
  McpServer,
  ResourceTemplate,
} from "@modelcontextprotocol/sdk/server/mcp.js";
// import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
// import { ServerRegistrationRequest } from "@modelcontextprotocol/sdk/shared/registry.js";
import { z } from "zod";
import express, { Request, Response } from "express";
import path from "path";
import { fileURLToPath } from "url";

const PORT_NUMBER = 8080;
// const serverParams: ServerRegistrationRequest = {
//   name: "CalculatorServer",
//   slug: "calculator-server",
//   description: "A simple calculator server",
//   provider: "Abhishek",
//   url: "https://c11a-18-29-222-203.ngrok-free.app",
//   types: ["tool"],
//   contact_email: "tremblerz@gmail.com",
// };

// Create an MCP server
const server = new McpServer(
  {
    name: "Demo",
    version: "1.0.0",
  }
  // ,{
  //   registry: {
  //     registryUrl: "http://localhost",
  //     apiKey: "your-api-key",
  //     registration: {},
  //   },
  // }
);

// Registers the server on the registry
// Submits the name and version of the server to the registry
// server.register();

// Fixing the schema to use ZodRawShape directly
const addSchema = { a: z.number(), b: z.number() };
const multiplySchema = { a: z.number(), b: z.number() };

// Updated tool registrations
server.tool("add", addSchema, async ({ a, b }) => ({
  content: [{ type: "text", text: String(a + b) }],
}));

server.tool("multiply", multiplySchema, async ({ a, b }) => ({
  content: [{ type: "text", text: String(a * b) }],
}));

// Add a dynamic greeting resource
server.resource(
  "greeting",
  new ResourceTemplate("greeting://{name}", { list: undefined }),
  async (uri, { name }) => ({
    contents: [
      {
        uri: uri.href,
        text: `Hello, ${name}!`,
      },
    ],
  })
);

const app = express();

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports: { [sessionId: string]: SSEServerTransport } = {};

// Add a counter to track the number of hits to the /messages endpoint
let messageHitCount = 0;

// Serve a simple HTML page with client-side code to connect to SSE
app.get("/", (_: Request, res: Response) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>MCP Calculator</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #output { margin-top: 20px; padding: 10px; border: 1px solid #ccc; }
      </style>
    </head>
    <body>
      <h1>MCP Calculator Server</h1>
      <p>Server is running correctly!</p>
      <button id="connectBtn">Connect to SSE</button>
      <div id="output">Connection status will appear here...</div>

      <script>
        document.getElementById('connectBtn').addEventListener('click', () => {
          const output = document.getElementById('output');
          output.textContent = 'Connecting to SSE...';

          const evtSource = new EventSource('/sse');

          evtSource.onopen = () => {
            output.textContent += '\\nConnected to SSE!';
          };

          evtSource.onerror = (err) => {
            output.textContent += '\\nError with SSE connection: ' + JSON.stringify(err);
            evtSource.close();
          };

          evtSource.onmessage = (event) => {
            output.textContent += '\\nReceived: ' + event.data;
          };
        });
      </script>
    </body>
    </html>
  `);
});

// Test endpoint to verify server is working
app.get("/api/test", (_: Request, res: Response) => {
  res.json({ status: "ok", message: "Server is working!" });
});

// MCP verification endpoint
app.get("/mcp-verification.txt", (_: Request, res: Response) => {
  res.type("text").send("qyO-WdhO07dpEEDumoCo4BthvwRKPP1DA-9Ohyg3xD8");
});

// SSE endpoint for MCP communication
app.get("/sse", async (req: Request, res: Response) => {
  const transport = new SSEServerTransport("/messages", res);
  transports[transport.sessionId] = transport;
  res.on("close", () => {
    delete transports[transport.sessionId];
  });
  await server.connect(transport);
});

app.post("/messages", async (req: Request, res: Response) => {
  // Increment the counter
  messageHitCount++;

  const sessionId = req.query.sessionId as string;
  const transport = transports[sessionId];
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(400).send("No transport found for sessionId");
  }
});

// Add an endpoint to retrieve the hit count
app.get("/messages/hit-count", (_: Request, res: Response) => {
  res.json({ hitCount: messageHitCount });
});

console.log(`Server starting on http://localhost:${PORT_NUMBER}`);
app.listen(PORT_NUMBER, () => {
  console.log(`Server running on http://localhost:${PORT_NUMBER}`);
});
