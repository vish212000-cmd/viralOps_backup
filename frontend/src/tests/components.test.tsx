import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

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
    expect(button).toHaveClass('button');

    rerender(<Button variant="secondary">Secondary Button</Button>);
    const secButton = screen.getByRole('button', { name: /secondary button/i });
    expect(secButton).toHaveClass('secondary');
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
    expect(input.style.borderColor).toBe('hsl(var(--danger))');
  });

  it('renders Badges with correct status mappings', () => {
    const { rerender } = render(<Badge status="COMPLETED" />);
    expect(screen.getByText('COMPLETED')).toHaveClass('badge-active');

    rerender(<Badge status="ACTIVE" />);
    expect(screen.getByText('ACTIVE')).toHaveClass('badge-active');

    rerender(<Badge status="PENDING" />);
    expect(screen.getByText('PENDING')).toHaveClass('badge-pending');
  });

  it('renders Card with glassmorphism styles', () => {
    render(<Card>Card Content</Card>);
    const card = screen.getByText('Card Content');
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('glass-panel');
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

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

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

    // Wait for the loader to clear and verify mock workspace views are present
    const header = await screen.findByText('Workspace Dashboard');
    expect(header).toBeInTheDocument();
    expect(screen.getByText('Your Projects')).toBeInTheDocument();
  });
});

// Import newly implemented page components for testing
const Sidebar = React.lazy(() => import('../components/Sidebar'));
const Billing = React.lazy(() => import('../pages/Billing'));
const Analytics = React.lazy(() => import('../pages/Analytics'));
const Policies = React.lazy(() => import('../pages/Policies'));

describe('Unified Sidebar Component', () => {
  it('renders logo and navigation links', async () => {
    render(
      <MemoryRouter>
        <React.Suspense fallback={<div>Loading...</div>}>
          <Sidebar />
        </React.Suspense>
      </MemoryRouter>
    );
    expect(await screen.findByText('Viral')).toBeInTheDocument();
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
