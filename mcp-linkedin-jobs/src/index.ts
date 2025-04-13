import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from "zod";
import type { Request, Response } from "express";
import { LinkedInService } from "./services/linkedin.service.js";
import { registerSearchTool } from "./tools/search.tool.js";

const app = express();
export const server = new McpServer({
  name: "LinkedIn Jobs",
  version: "1.0.0"
});

// Register the search tool
registerSearchTool(server);

// Remove the test searchJobs tool since we now have the real implementation
server.tool("hello", { name: z.string().optional() }, async ({ name }) => ({
  content: [{ type: "text", text: `Hello ${name || 'world'}!` }],
}));

// Basic CORS setup
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// Store transports for multiple connections
const transports: Record<string, SSEServerTransport> = {};

// SSE endpoint
app.get("/sse", async (req: Request, res: Response) => {
  const transport = new SSEServerTransport('/messages', res);

  transports[transport.sessionId] = transport;
  // simple debug log
  console.log(`[DEBUG] New connection: ${transport.sessionId}`);

  res.on("close", () => {
    delete transports[transport.sessionId];
    console.log(`[DEBUG] Connection closed: ${transport.sessionId}`);
  });

  await server.connect(transport);
});

// Message endpoint
app.post("/messages", async (req: Request, res: Response) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports[sessionId];

  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(400).send('No transport found for sessionId');
  }
});

const port = 3002;
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});


// linkedin jobs api tester endpoint
app.get("/linkedin-jobs", async (req: Request, res: Response) => {
  const linkedinService = LinkedInService.getInstance();
  const response = await linkedinService.searchJobs({ keyword: "software engineer" });
  res.json(response);
});
