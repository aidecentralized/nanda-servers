import { LinkedInJob } from '../types/linkedin.types.js';

export class JobCacheService {
    private static instance: JobCacheService;
    private cache: Map<string, { data: LinkedInJob[]; timestamp: number }>;
    private readonly TTL = 5 * 60 * 1000; // 5 minutes cache TTL

    private constructor() {
        this.cache = new Map();
    }

    public static getInstance(): JobCacheService {
        if (!JobCacheService.instance) {
            JobCacheService.instance = new JobCacheService();
        }
        return JobCacheService.instance;
    }

    public set(key: string, data: LinkedInJob[]): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    public get(key: string): LinkedInJob[] | null {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.TTL) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    public clear(): void {
        this.cache.clear();
    }
}
