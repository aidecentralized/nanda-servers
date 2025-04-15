import { createRequire } from 'module';
import { QueryOptions, LinkedInJob } from '../types/linkedin.types.js';
// import { JobCacheService } from './cache.service.js';

const require = createRequire(import.meta.url);
const linkedIn = require('linkedin-jobs-api');
// const cache = JobCacheService.getInstance();


export class LinkedInService {
    private static instance: LinkedInService;

    private constructor() {}

    public static getInstance(): LinkedInService {
        if (!LinkedInService.instance) {
            LinkedInService.instance = new LinkedInService();
        }
        return LinkedInService.instance;
    }

    // private getCacheKey(options: QueryOptions): string {
    //     return JSON.stringify(options);
    // }

    public async searchJobs(options: QueryOptions): Promise<LinkedInJob[]> {
        // const cacheKey = this.getCacheKey(options);
        // const cachedData = cache.get(cacheKey);

        // if (cachedData) {
        //     return cachedData;
        // }

        try {
            const results = await linkedIn.query(options);
            // cache.set(cacheKey, results);
            return results;
        } catch (error) {
            console.error('Error fetching jobs:', error);
            throw new Error('Failed to fetch jobs from LinkedIn');
        }
    }
}
