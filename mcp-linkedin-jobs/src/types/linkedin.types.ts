// Types based on the LinkedIn Jobs API response
export interface LinkedInJob {
    position: string;
    company: string;
    companyLogo: string;
    location: string;
    date: string;
    agoTime: string;
    salary: string;
    jobUrl: string;
}

export interface QueryOptions {
    keyword?: string;
    location?: string;
    dateSincePosted?: 'past month' | 'past week' | '24hr';
    jobType?: 'full time' | 'part time' | 'contract' | 'temporary' | 'volunteer' | 'internship';
    remoteFilter?: 'on site' | 'remote' | 'hybrid';
    salary?: string;
    experienceLevel?: 'internship' | 'entry level' | 'associate' | 'senior' | 'director' | 'executive';
    limit?: string;
    sortBy?: 'recent' | 'relevant';
    page?: string;
}

export interface JsonApiResponse {
    data: {
        type: string;
        id: string;
        attributes: Omit<LinkedInJob, 'id'>;
        links: {
            self: string;
        };
    }[];
    meta: {
        total: number;
        page: number;
        limit: number;
        searchCriteria: Record<string, unknown>;
    };
    jsonapi: {
        version: string;
    };
}