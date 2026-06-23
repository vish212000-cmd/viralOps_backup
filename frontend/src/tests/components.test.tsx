import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { api } from '../utils/api';

// Import design system components
import { Button } from '../components/design/Button';
import { Input } from '../components/design/Input';
import { Badge } from '../components/design/Badge';
import { Card } from '../components/design/Card';

// Import Layout/Page components
import ErrorBoundary from '../components/ErrorBoundary';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';

// Mock contexts
import { ToastProvider } from '../context/ToastContext';

const mockLoginUser = vi.fn().mockResolvedValue(undefined);
const mockRegisterUser = vi.fn().mockResolvedValue(undefined);
const mockLogoutUser = vi.fn();
const mockSelectOrg = vi.fn();
const mockLoadWorkspaces = vi.fn().mockResolvedValue(undefined);

// Mock the useAuth hook
vi.mock('../context/AuthContext', () => {
  return {
    useAuth: () => ({
      user: { username: 'testcreator', email: 'test@viralops.com' },
      orgs: [{ id: 1, name: 'Test Org', slug: 'test-org', created_at: '' }],
      currentOrg: { id: 1, name: 'Test Org', slug: 'test-org', created_at: '' },
      loading: false,
      loginUser: mockLoginUser,
      registerUser: mockRegisterUser,
      logoutUser: mockLogoutUser,
      selectOrg: mockSelectOrg,
      loadWorkspaces: mockLoadWorkspaces,
    }),
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// Mock the API service
vi.mock('../utils/api', () => {
  return {
    api: {
      token: 'test-token',
      orgSlug: 'test-org',
      setToken: vi.fn(),
      setOrgSlug: vi.fn(),
      get: vi.fn().mockResolvedValue([]),
      post: vi.fn().mockResolvedValue({}),
      put: vi.fn().mockResolvedValue({}),
      patch: vi.fn().mockResolvedValue({}),
      delete: vi.fn().mockResolvedValue({}),
    }
  };
});

describe('Reusable Design System Components', () => {
  it('renders Button with correct content and classes', () => {
    const { rerender } = render(<Button>Click Me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-accent-primary');

    rerender(<Button variant="secondary">Secondary Button</Button>);
    const secButton = screen.getByRole('button', { name: /secondary button/i });
    expect(secButton).toHaveClass('bg-white/5');
  });

  it('renders Input with labels and displays errors when validated', () => {
    render(
      <Input
        label="Username"
        error="Username must be unique"
        value=""
        onChange={() => {}}
      />
    );
    expect(screen.getByText('Username')).toBeInTheDocument();
    expect(screen.getByText('Username must be unique')).toBeInTheDocument();
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input).toHaveClass('border-danger');
  });

  it('renders Badges with correct status mappings', () => {
    const { rerender } = render(<Badge status="COMPLETED" />);
    expect(screen.getByText('COMPLETED')).toHaveClass('text-success');

    rerender(<Badge status="ACTIVE" />);
    expect(screen.getByText('ACTIVE')).toHaveClass('text-success');

    rerender(<Badge status="PENDING" />);
    expect(screen.getByText('PENDING')).toHaveClass('text-warning');
  });

  it('renders Card with glassmorphism styles', () => {
    render(<Card>Card Content</Card>);
    const card = screen.getByText('Card Content');
    expect(card).toBeInTheDocument();
    expect(card.parentElement).toHaveClass('bg-bg-elevated/65');
  });
});

describe('ErrorBoundary Component', () => {
  it('catches render errors and displays fallback screen', () => {
    const ProblemComponent = () => {
      throw new Error('Simulation Crash');
    };

    // Suppress console.error in tests for this block to keep test logs clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Application Render Crash')).toBeInTheDocument();
    expect(screen.getByText(/simulation crash/i)).toBeInTheDocument();
    consoleSpy.mockRestore();
  });
});

describe('Login Page', () => {
  it('renders input fields and responds to typing', async () => {
    render(
      <MemoryRouter>
        <ToastProvider>
          <Login />
        </ToastProvider>
      </MemoryRouter>
    );

    const usernameInput = screen.getByLabelText(/Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitButton = screen.getByRole('button', { name: /Sign In/i });

    expect(usernameInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
    expect(submitButton).toBeInTheDocument();

    fireEvent.change(usernameInput, { target: { value: 'testcreator' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(usernameInput).toHaveValue('testcreator');
    expect(passwordInput).toHaveValue('password123');
  });
});

describe('Dashboard Page', () => {
  it('renders workspace selector and projects list', async () => {
    render(
      <MemoryRouter>
        <ToastProvider>
          <Dashboard />
        </ToastProvider>
      </MemoryRouter>
    );

    // The user should now be redirected to the dashboard which says Home
    const header = await screen.findByText('Home');
    expect(header).toBeInTheDocument();
    expect(screen.getByText('Your Content')).toBeInTheDocument();
  });
});

// Import newly implemented page components for testing
import Sidebar from '../components/Sidebar';
import Billing from '../pages/Billing';
import Analytics from '../pages/Analytics';
import Policies from '../pages/Policies';

describe('Unified Sidebar Component', () => {
  beforeEach(() => {
    window.innerWidth = 1280;
    window.dispatchEvent(new Event('resize'));
  });

  it('renders logo and navigation links', async () => {
    render(
      <MemoryRouter>
        <React.Suspense fallback={<div>Loading...</div>}>
          <Sidebar />
        </React.Suspense>
      </MemoryRouter>
    );
    expect(await screen.findByText('Viral', { exact: false })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /projects/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /brand voice/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /analytics/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /billing/i })).toBeInTheDocument();
  });
});

describe('Workspace Billing Settings Page', () => {
  it('renders quota cards and plan pricing cards', async () => {
    render(
      <MemoryRouter>
        <ToastProvider>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Billing />
          </React.Suspense>
        </ToastProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText('Workspace Billing Settings')).toBeInTheDocument();
    expect(screen.getByText('Projects Limit')).toBeInTheDocument();
    expect(screen.getByText('AI Content Generations')).toBeInTheDocument();
    expect(screen.getByText('Available Subscription Plans')).toBeInTheDocument();
    expect(screen.getByText('Indian GST & Invoicing Info')).toBeInTheDocument();
  });
});

describe('Workspace Analytics Page', () => {
  it('renders operational KPIs and trends SVG charts', async () => {
    render(
      <MemoryRouter>
        <ToastProvider>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Analytics />
          </React.Suspense>
        </ToastProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText('Workspace Analytics')).toBeInTheDocument();
    expect(screen.getByText('Total AI Generations')).toBeInTheDocument();
    expect(screen.getByText('Job Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Avg Processing Time')).toBeInTheDocument();
  });
});

describe('Legal Policies Pages', () => {
  it('renders Terms of Service policy details', async () => {
    render(
      <React.Suspense fallback={<div>Loading...</div>}>
        <Policies page="terms" />
      </React.Suspense>
    );
    expect(await screen.findByText('Terms of Service')).toBeInTheDocument();
    expect(screen.getByText(/1\. Acceptance of Terms/i)).toBeInTheDocument();
  });

  it('renders Privacy Policy details', async () => {
    render(
      <React.Suspense fallback={<div>Loading...</div>}>
        <Policies page="privacy" />
      </React.Suspense>
    );
    expect(await screen.findByText('Privacy Policy')).toBeInTheDocument();
    expect(screen.getByText(/1\. Information We Collect/i)).toBeInTheDocument();
  });

  it('renders Refund and Cancellation policy details', async () => {
    render(
      <React.Suspense fallback={<div>Loading...</div>}>
        <Policies page="refund" />
      </React.Suspense>
    );
    expect(await screen.findByText('Refund & Cancellation Policy')).toBeInTheDocument();
    expect(screen.getByText(/1\. Cancellations/i)).toBeInTheDocument();
  });
});

const GoogleCallback = React.lazy(() => import('../pages/GoogleCallback'));
const ProjectDetails = React.lazy(() => import('../pages/ProjectDetails'));

describe('Google OAuth Callback Page', () => {
  it('renders loading state first and exchanges code', async () => {
    const mockPost = vi.spyOn(api, 'post').mockResolvedValue({
      access: 'mock-access',
      refresh: 'mock-refresh',
      user: { username: 'oauth_user', email: 'oauth@viralops.com' }
    });

    render(
      <MemoryRouter initialEntries={['/auth/google/callback?code=mock_google_code']}>
        <ToastProvider>
          <React.Suspense fallback={<div>Loading...</div>}>
            <GoogleCallback />
          </React.Suspense>
        </ToastProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Verifying credentials...')).toBeInTheDocument();
    
    await vi.waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/auth/google/', {
        code: 'mock_google_code',
        redirect_uri: expect.stringContaining('/auth/google/callback')
      });
    });

    mockPost.mockRestore();
  });

  it('renders error state when google authorization is rejected', async () => {
    render(
      <MemoryRouter initialEntries={['/auth/google/callback?error=access_denied']}>
        <ToastProvider>
          <React.Suspense fallback={<div>Loading...</div>}>
            <GoogleCallback />
          </React.Suspense>
        </ToastProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Authentication Error')).toBeInTheDocument();
    expect(screen.getByText(/access_denied/i)).toBeInTheDocument();
  });
});

describe('Project Details Page', () => {
  it('renders project details, tabs, and publish action', async () => {
    const mockGet = vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url.includes('/assets/')) {
        return Promise.resolve([
          {
            id: 1,
            project: 1,
            type: 'HOOK',
            platform: 'MULTI',
            content: 'This is a hook asset.',
            is_favorite: false,
            publish_records: []
          }
        ]);
      }
      if (url.includes('/sources/')) {
        return Promise.resolve([
          {
            id: 1,
            project: 1,
            type: 'VIDEO',
            title: 'AI Video',
            status: 'COMPLETED',
            file_name: 'test.mp4',
            text_content: 'This is the transcription text.'
          }
        ]);
      }
      if (url.includes('/projects/')) {
        return Promise.resolve({
          id: 1,
          name: 'Social Launch Video',
          description: 'A video detailing the new AI strategy.',
          status: 'COMPLETED',
          created_at: '',
          updated_at: ''
        });
      }
      return Promise.resolve([]);
    });

    render(
      <MemoryRouter initialEntries={['/projects/1']}>
        <ToastProvider>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Routes>
              <Route path="/projects/:projectId" element={<ProjectDetails />} />
            </Routes>
          </React.Suspense>
        </ToastProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Social Launch Video')).toBeInTheDocument();
    expect(screen.getByText('This is a hook asset.')).toBeInTheDocument();
    
    const publishBtn = screen.getByTitle('Publish Asset');
    expect(publishBtn).toBeInTheDocument();

    fireEvent.click(publishBtn);
    expect(screen.getByText('Publish Asset to Social')).toBeInTheDocument();
    expect(screen.getByText('Twitter / X')).toBeInTheDocument();
    expect(screen.getByText('YouTube Shorts')).toBeInTheDocument();

    mockGet.mockRestore();
  });
});
