import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Billing from '../pages/Billing';
import { billingApi } from '../services/billingApi';
import { ToastProvider } from '../context/ToastContext';

vi.mock('../context/AuthContext', () => {
  const mockCurrentOrg = { id: 1, name: 'Test Org', slug: 'test-org' };
  const mockOrgs = [mockCurrentOrg];
  const mockUser = { username: 'testuser', email: 'test@viralops.com' };
  
  return {
    useAuth: () => ({
      user: mockUser,
      orgs: mockOrgs,
      currentOrg: mockCurrentOrg,
      logoutUser: vi.fn(),
      selectOrg: vi.fn(),
      loadWorkspaces: vi.fn(),
    }),
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// Mock the billing API
vi.mock('../services/billingApi', () => {
  return {
    billingApi: {
      getPlans: vi.fn(),
      getMySubscription: vi.fn(),
      getHistory: vi.fn(),
      updateDetails: vi.fn(),
      createSubscription: vi.fn(),
      verifyPayment: vi.fn(),
      cancelSubscription: vi.fn(),
    }
  };
});

const mockPlans = [
  { id: 1, name: 'Free Trial', price_monthly: '0', price_yearly: '0', max_projects: 3, max_generations_per_month: 10 },
  { id: 2, name: 'Pro', price_monthly: '2999', price_yearly: '29990', max_projects: 999999, max_generations_per_month: 100 }
];

const mockSubscription = {
  id: 1,
  plan: mockPlans[0],
  status: 'ACTIVE',
  legal_name: 'Acme Corp',
  billing_contact: '1234567890',
  billing_email: 'billing@acme.com',
  billing_address: '123 Acme Street',
  gstin: '29AAAAA1111A1Z1',
  usage: {
    projects: 1,
    limit_projects: 3,
    generations: 5,
    limit_generations: 10,
  }
};

const mockHistory = {
  payments: [],
  invoices: [
    {
      id: 1,
      invoice_number: 'INV-2026-001',
      amount: '3538.82',
      tax_amount: '539.82',
      gstin: '29AAAAA1111A1Z1',
      legal_name: 'Acme Corp',
      billing_address: '123 Acme Street',
      created_at: '2026-01-01T10:00:00Z'
    }
  ]
};

describe('Billing Page', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (billingApi.getPlans as any).mockResolvedValue(mockPlans);
    (billingApi.getMySubscription as any).mockResolvedValue(mockSubscription);
    (billingApi.getHistory as any).mockResolvedValue(mockHistory);
    (window as any).Razorpay = vi.fn();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders billing page and loads data', async () => {
    render(
      <MemoryRouter>
        <ToastProvider>
          <main>
            <Billing />
          </main>
        </ToastProvider>
      </MemoryRouter>
    );

    // Initial loading state
    expect(screen.getByRole('main')).toBeInTheDocument();

    // Wait for the data to load
    await waitFor(() => {
      expect(screen.getByText('Workspace Billing Settings')).toBeInTheDocument();
    });

    // Check if plans are rendered
    expect(screen.getByText('Free Trial')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();

    // Check if usage is displayed correctly
    expect(screen.getByText('1 / 3')).toBeInTheDocument(); // Projects
    expect(screen.getByText('5 / 10')).toBeInTheDocument(); // Generations

    // Check if invoices are displayed
    expect(screen.getByText('INV-2026-001')).toBeInTheDocument();
    expect(screen.getByText('₹3538')).toBeInTheDocument();
  });

  it('allows updating GST compliance details', async () => {
    (billingApi.updateDetails as any).mockResolvedValue({ ...mockSubscription, legal_name: 'New Acme Corp' });

    render(
      <MemoryRouter>
        <ToastProvider>
          <main>
            <Billing />
          </main>
        </ToastProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Workspace Billing Settings')).toBeInTheDocument();
    });

    const legalNameInput = screen.getByLabelText(/Registered Legal Entity Name/i) as HTMLInputElement;
    fireEvent.change(legalNameInput, { target: { value: 'New Acme Corp' } });
    
    const updateButton = screen.getByRole('button', { name: /Update Invoice Details/i });
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(billingApi.updateDetails).toHaveBeenCalledWith({
        legal_name: 'New Acme Corp',
        billing_contact: '1234567890',
        billing_email: 'billing@acme.com',
        billing_address: '123 Acme Street',
        gstin: '29AAAAA1111A1Z1',
      });
    });
  });

  it('triggers checkout simulation for testing offline fallback', async () => {
    // Mock the createSubscription call to return a test mock key
    (billingApi.createSubscription as any).mockResolvedValue({
      order_id: 'order_mock_123',
      amount: 299900,
      currency: 'INR',
      key_id: 'rzp_test_mock_key',
      status: 'CREATED'
    });

    render(
      <MemoryRouter>
        <ToastProvider>
          <main>
            <Billing />
          </main>
        </ToastProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Pro')).toBeInTheDocument();
    });

    // Find the "Select Plan" button for the Pro plan
    const buttons = screen.getAllByRole('button', { name: /Select Plan/i });
    fireEvent.click(buttons[0]);

    // Should open the Sandbox Payment Simulation modal
    await waitFor(() => {
      expect(screen.getByText('Sandbox Payment Simulation')).toBeInTheDocument();
    });

    // Confirm mock payment
    (billingApi.verifyPayment as any).mockResolvedValue({});
    const confirmButton = screen.getByRole('button', { name: /Confirm Success Mock Payment/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(billingApi.verifyPayment).toHaveBeenCalledWith(
        'order_mock_123',
        expect.any(String),
        'mock_signature',
        2 // plan_id
      );
    });
  });
});
