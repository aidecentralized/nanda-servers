#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import express, { Request, Response } from "express";

const PORT_NUMBER = 8080;

// Zod schema for joke tool (no input required)
const JokeArgumentsSchema = z.object({});

// Create MCP Server
const server = new Server(
  {
    name: "joke-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get-joke",
        description: "Get a random programming joke",
        inputSchema: {
          type: "object",
          properties: {},
          required: [],
        },
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "get-joke") {
      JokeArgumentsSchema.parse(args);

      const jokeUrl = "https://official-joke-api.appspot.com/jokes/programming/random";
      const response = await fetch(jokeUrl);
      const jokeData = await response.json();

      const joke = jokeData?.[0];
      if (!joke) {
        return {
          content: [{ type: "text", text: "No joke found!" }],
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `Here's a programming joke:\n\n${joke.setup}\n${joke.punchline}`,
          },
        ],
      };
    } else {
      throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error(
        `Invalid arguments: ${error.errors
          .map((e) => `${e.path.join(".")}: ${e.message}`)
          .join(", ")}`
      );
    }
    throw error;
  }
});

// Setup Express and SSE
const app = express();
const transports: { [sessionId: string]: SSEServerTransport } = {};
let messageHitCount = 0;

app.get("/", (_: Request, res: Response) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>MCP Joke Server</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #output { margin-top: 20px; padding: 10px; border: 1px solid #ccc; }
      </style>
    </head>
    <body>
      <h1>MCP Joke Server</h1>
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

// Health check
app.get("/api/test", (_: Request, res: Response) => {
  res.json({ status: "ok", message: "Joke server is working!" });
});

// SSE handshake
app.get("/sse", async (req: Request, res: Response) => {
  const transport = new SSEServerTransport("/messages", res);
  transports[transport.sessionId] = transport;
  res.on("close", () => {
    delete transports[transport.sessionId];
  });
  await server.connect(transport);
});

app.post("/messages", async (req: Request, res: Response) => {
  messageHitCount++;
  const sessionId = req.query.sessionId as string;
  const transport = transports[sessionId];
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(400).send("No transport found for sessionId");
  }
});

app.get("/messages/hit-count", (_: Request, res: Response) => {
  res.json({ hitCount: messageHitCount });
});

// Start the server
async function main() {
  console.log(`Joke MCP Server starting on http://localhost:${PORT_NUMBER}`);
  app.listen(PORT_NUMBER, () => {
    console.log(`Joke MCP Server running on http://localhost:${PORT_NUMBER}`);
  });
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
