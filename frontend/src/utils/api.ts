const BASE_URL = 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

interface FileResponse {
  isFile: true;
  blob: Blob;
  response: Response;
}

function getCSRFToken(): string | null {
  const matches = document.cookie.match(/csrftoken=([^;]+)/);
  return matches ? matches[1] : null;
}

class ApiClient {
  public token: string | null;
  public orgSlug: string | null;

  constructor() {
    this.token = localStorage.getItem('access_token') || null;
    this.orgSlug = localStorage.getItem('current_org_slug') || null;
  }

  public setToken(token: string | null): void {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  public setOrgSlug(slug: string | null): void {
    this.orgSlug = slug;
    if (slug) {
      localStorage.setItem('current_org_slug', slug);
    } else {
      localStorage.removeItem('current_org_slug');
    }
  }

  public async request(endpoint: string, options: RequestOptions = {}): Promise<any> {
    const url = `${BASE_URL}${endpoint}`;
    
    const headers: Record<string, string> = {
      ...options.headers,
    };

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = options.headers?.['Content-Type'] || 'application/json';
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (this.orgSlug) {
      headers['X-Org-Slug'] = this.orgSlug;
    }

    const method = options.method || 'GET';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition && contentDisposition.includes('attachment')) {
        const blob = await response.blob();
        return { isFile: true, blob, response } as FileResponse;
      }

      if (response.status === 401) {
        this.setToken(null);
        window.dispatchEvent(new Event('auth-expired'));
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw { status: response.status, data: errorData };
      }

      return response.status === 204 ? null : await response.json();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  public get(endpoint: string, options: RequestOptions = {}): Promise<any> {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  public post(endpoint: string, body?: any, options: RequestOptions = {}): Promise<any> {
    const isFormData = body instanceof FormData;
    return this.request(endpoint, { 
      ...options, 
      method: 'POST', 
      body: isFormData ? body : (body ? JSON.stringify(body) : undefined) 
    });
  }

  public put(endpoint: string, body: any, options: RequestOptions = {}): Promise<any> {
    return this.request(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: JSON.stringify(body) 
    });
  }

  public patch(endpoint: string, body: any, options: RequestOptions = {}): Promise<any> {
    return this.request(endpoint, { 
      ...options, 
      method: 'PATCH', 
      body: JSON.stringify(body) 
    });
  }

  public delete(endpoint: string, options: RequestOptions = {}): Promise<any> {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

export const api = new ApiClient();
export type { FileResponse };
export type { RequestOptions };
