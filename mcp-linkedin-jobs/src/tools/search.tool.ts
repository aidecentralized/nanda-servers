import { z } from 'zod';
import { LinkedInService } from '../services/linkedin.service.js';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
// Define the schema as a proper Zod object schema
const searchParamsSchema = z.object({
    keyword: z.string().optional(),
    location: z.string().optional(),
    dateSincePosted: z.enum(['past month', 'past week', '24hr']).optional(),
    jobType: z.enum(['full time', 'part time', 'contract', 'temporary', 'volunteer', 'internship']).optional(),
    remoteFilter: z.enum(['on site', 'remote', 'hybrid']).optional(),
    experienceLevel: z.enum(['internship', 'entry level', 'associate', 'senior', 'director', 'executive']).optional(),
    limit: z.string().optional().default('10'),
    page: z.string().optional().default('0')
});

export const registerSearchTool = (server: McpServer) => {
    server.tool(
        'linkedin-search',
        'Search for jobs on LinkedIn with various filters',
        searchParamsSchema.shape, // Use .shape for the raw schema object
        async (args): Promise<CallToolResult> => {
            const linkedInService = LinkedInService.getInstance();

            try {
                const jobs = await linkedInService.searchJobs(args);

                return {
                    content: [
                        {
                            type: "text" as const,
                            text: `Found ${jobs.length} jobs:`
                        },
                        ...jobs.map(job => ({
                            type: "text" as const,
                            text: JSON.stringify(job)
                        }))
                    ]
                };
            } catch (error) {
                return {
                    content: [{
                        type: "text" as const,
                        text: `Error searching jobs: ${error instanceof Error ? error.message : 'Unknown error'}`
                    }],
                    isError: true
                };
            }
        }
    );
};
