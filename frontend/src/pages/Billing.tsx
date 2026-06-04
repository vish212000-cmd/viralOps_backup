import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { billingApi } from '../services/billingApi';
import Sidebar from '../components/Sidebar';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { Input } from '../components/design/Input';
import { Badge } from '../components/design/Badge';
import { 
  CreditCard, CheckCircle2, AlertTriangle, FileText, 
  HelpCircle, Receipt, Loader2, ArrowRight
} from 'lucide-react';

interface Plan {
  id: number;
  name: string;
  price_monthly: string;
  price_yearly: string;
  max_projects: number;
  max_generations_per_month: number;
}

interface Subscription {
  id: number;
  plan: Plan;
  status: string;
  start_date: string;
  end_date: string;
  legal_name: string;
  billing_contact: string;
  billing_email: string;
  billing_address: string;
  gstin: string;
  razorpay_subscription_id: string;
  organization?: {
    name: string;
    billing_email?: string;
    slug: string;
  };
}

interface Usage {
  projects: number;
  generations: number;
  limit_projects: number;
  limit_generations: number;
}

interface PaymentRecord {
  id: number;
  razorpay_payment_id: string;
  amount: string;
  currency: string;
  status: string;
  created_at: string;
}

interface InvoiceRecord {
  id: number;
  invoice_number: string;
  amount: string;
  tax_amount: string;
  gstin: string;
  legal_name: string;
  billing_address: string;
  created_at: string;
}

export default function Billing() {
  const { currentOrg, user } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [history, setHistory] = useState<{ payments: PaymentRecord[]; invoices: InvoiceRecord[] }>({ payments: [], invoices: [] });

  // India-ready compliance details form states
  const [legalName, setLegalName] = useState('');
  const [billingContact, setBillingContact] = useState('');
  const [billingEmail, setBillingEmail] = useState('');
  const [billingAddress, setBillingAddress] = useState('');
  const [gstin, setGstin] = useState('');

  // Local dialog/modal for simulating payment in offline runs
  const [mockCheckoutData, setMockCheckoutData] = useState<{ subscription_id: string; amount: number; plan_id: number } | null>(null);

  useEffect(() => {
    if (currentOrg) {
      loadBillingData();
    }
  }, [currentOrg]);

  const loadBillingData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Plans
      const plansList = await billingApi.getPlans() as unknown as Plan[];
      setPlans(plansList);

      // 2. Fetch Active Subscription & Usage Status
      const subRes = await billingApi.getMySubscription() as any;
      setSubscription(subRes || null);
      setUsage(subRes?.usage || null);

      // Set form details
      setLegalName(subRes?.legal_name || '');
      setBillingContact(subRes?.billing_contact || '');
      setBillingEmail(subRes?.billing_email || user?.email || '');
      setBillingAddress(subRes?.billing_address || '');
      setGstin(subRes?.gstin || '');

      // 3. Fetch Payment and Invoice Records
      const historyRes = await billingApi.getHistory();
      setHistory(historyRes);
    } catch (err) {
      console.error(err);
      showToast('Failed to load workspace billing details.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadRazorpayScript = (): Promise<boolean> => {
    return new Promise((resolve) => {
      if ((window as any).Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleUpdateGSTDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (gstin && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(gstin.toUpperCase())) {
      showToast('Please enter a valid 15-digit GSTIN (e.g. 22AAAAA1111A1Z1).', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await billingApi.updateDetails({
        legal_name: legalName,
        billing_contact: billingContact,
        billing_email: billingEmail,
        billing_address: billingAddress,
        gstin: gstin.toUpperCase(),
      });
      showToast('Billing compliance details updated!', 'success');
      loadBillingData();
    } catch (err) {
      console.error(err);
      showToast('Failed to update GST compliance details.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheckout = async (plan: Plan) => {
    if (plan.id === subscription?.plan?.id && subscription.status === 'ACTIVE') {
      showToast('You are already subscribed to this plan!', 'info');
      return;
    }

    setSubmitting(true);
    try {
      const res = await billingApi.createSubscription(plan.id) as any;

      if (res.status === 'ACTIVE') {
        showToast('Successfully switched to ' + plan.name + ' plan!', 'success');
        loadBillingData();
        return;
      }

      // Try triggering Razorpay Checkout
      const scriptLoaded = await loadRazorpayScript();
      
      if (!scriptLoaded || res.key_id === 'rzp_test_mock_key') {
        // Fallback: Sandbox Simulation Mode (for local development or when Razorpay script is blocked)
        setMockCheckoutData({
          subscription_id: res.order_id,
          amount: parseFloat(plan.price_monthly),
          plan_id: plan.id
        });
        setSubmitting(false);
        return;
      }

      const options = {
        key: res.key_id,
        order_id: res.order_id,
        amount: res.amount,
        currency: res.currency || 'INR',
        name: 'ViralOps Content Engine',
        description: `Upgrade to ${plan.name} Plan`,
        handler: async (response: any) => {
          setSubmitting(true);
          try {
            await billingApi.verifyPayment(
              res.order_id,
              response.razorpay_payment_id,
              response.razorpay_signature,
              plan.id
            );
            showToast('Subscription payment processed successfully!', 'success');
            loadBillingData();
          } catch (err) {
            console.error(err);
            showToast('Payment verification failed. Contact support.', 'error');
          } finally {
            setSubmitting(false);
          }
        },
        prefill: {
          name: user?.username || 'Customer',
          email: billingEmail || user?.email || '',
          contact: billingContact
        },
        theme: {
          color: '#7c3aed'
        }
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } catch (err) {
      console.error(err);
      showToast('Checkout session failed to initialize.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulateMockPayment = async () => {
    if (!mockCheckoutData) return;
    setSubmitting(true);
    try {
      await billingApi.verifyPayment(
        mockCheckoutData.subscription_id,
        `pay_mock_${Date.now()}`,
        'mock_signature',
        mockCheckoutData.plan_id
      );
      showToast('Mock Payment Simulated & verified successfully!', 'success');
      setMockCheckoutData(null);
      loadBillingData();
    } catch (err) {
      console.error(err);
      showToast('Mock payment verification failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm("Are you sure you want to cancel your current subscription plan? All active limits will fallback to Free Trial limits at end of billing cycle.")) return;
    
    setSubmitting(true);
    try {
      await billingApi.cancelSubscription('User requested cancellation');
      showToast('Subscription cancelled successfully.', 'success');
      loadBillingData();
    } catch (err) {
      console.error(err);
      showToast('Failed to cancel subscription.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const downloadInvoice = (invoice: InvoiceRecord) => {
    // Generate simple PDF-like HTML print/download representation
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    
    const html = `
      <html>
        <head>
          <title>Invoice - ${invoice.invoice_number}</title>
          <style>
            body { font-family: sans-serif; padding: 40px; color: #333; }
            .header { display: flex; justify-content: space-between; border-bottom: 2px solid #7c3aed; padding-bottom: 20px; margin-bottom: 40px; }
            .invoice-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
            th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background-color: #f3f4f6; }
            .total { font-size: 1.25rem; font-weight: bold; text-align: right; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h1 style="color: #7c3aed; margin: 0;">ViralOps</h1>
              <p>Social Repurposing Engine</p>
            </div>
            <div style="text-align: right;">
              <h2 style="margin: 0;">INVOICE</h2>
              <p>No: ${invoice.invoice_number}</p>
              <p>Date: ${new Date(invoice.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          <div class="invoice-details">
            <div>
              <h3>Billed From:</h3>
              <p><strong>ViralOps India Ltd.</strong></p>
              <p>Bangalore, Karnataka, India</p>
              <p>GSTIN: 29AAACV1209B1Z4</p>
            </div>
            <div>
              <h3>Billed To:</h3>
              <p><strong>${invoice.legal_name || 'Individual Customer'}</strong></p>
              <p>${invoice.billing_address || 'No Billing Address Provided'}</p>
              <p>GSTIN: ${invoice.gstin || 'N/A'}</p>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Rate</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>ViralOps Workspace Subscription - monthly access</td>
                <td>1</td>
                <td>₹${(parseFloat(invoice.amount) - parseFloat(invoice.tax_amount)).toFixed(2)}</td>
                <td>₹${(parseFloat(invoice.amount) - parseFloat(invoice.tax_amount)).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Integrated 18% B2B GST Tax</td>
                <td>1</td>
                <td>₹${parseFloat(invoice.tax_amount).toFixed(2)}</td>
                <td>₹${parseFloat(invoice.tax_amount).toFixed(2)}</td>
              </tr>
            </tbody>
          </table>
          <div class="total">
            Total Amount Due: ₹${parseFloat(invoice.amount).toFixed(2)}
          </div>
          <p style="margin-top: 60px; font-size: 0.85rem; color: #666; text-align: center;">This is a computer-generated tax-invoice and requires no signature.</p>
        </body>
      </html>
    `;
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.print();
  };

  if (loading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader2 className="loading-spinner" size={40} />
        </main>
      </div>
    );
  }

  // Quotas Calculations
  const activePlanName = subscription?.plan?.name || 'Free Trial';
  const subStatus = subscription?.status || 'ACTIVE';
  const maxProjects = usage?.limit_projects || 3;
  const currentProjects = usage?.projects || 0;
  const maxGenerations = usage?.limit_generations || 10;
  const currentGenerations = usage?.generations || 0;

  const projectsPercent = Math.min((currentProjects / maxProjects) * 100, 100);
  const gensPercent = Math.min((currentGenerations / maxGenerations) * 100, 100);

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="main-content">
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Workspace Billing Settings</h1>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginTop: '0.25rem' }}>
            Manage organization subscription plans, quotas, and GST-compliant invoices.
          </p>
        </header>

        {subStatus !== 'ACTIVE' && (
          <div style={{ background: 'hsl(var(--warning) / 0.1)', border: '1px solid hsl(var(--warning) / 0.3)', padding: '1rem', borderRadius: '12px', color: 'hsl(var(--warning))', display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '2rem' }}>
            <AlertTriangle size={20} />
            <span>
              Your subscription is currently <strong>{subStatus}</strong>. Upgrade or complete payment to reactivate active quota limits.
            </span>
          </div>
        )}

        {/* Quota Limits Progress Cards */}
        <section className="bento-grid" style={{ marginBottom: '2.5rem' }}>
          <Card style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', color: 'hsl(var(--text-muted))', display: 'flex', justifyContent: 'space-between' }}>
              <span>Projects Limit</span>
              <span style={{ color: 'hsl(var(--text-primary))' }}>{currentProjects} / {maxProjects === 999999 ? 'Unlimited' : maxProjects}</span>
            </h3>
            <div style={{ width: '100%', height: '8px', background: 'hsl(var(--border-muted))', borderRadius: '99px', overflow: 'hidden', marginBottom: '0.75rem' }}>
              <div style={{ width: `${maxProjects === 999999 ? 0 : projectsPercent}%`, height: '100%', background: 'linear-gradient(90deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', borderRadius: '99px' }} />
            </div>
            <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-dim))' }}>
              Used to create workspaces and scope content pipeline projects.
            </p>
          </Card>

          <Card style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', color: 'hsl(var(--text-muted))', display: 'flex', justifyContent: 'space-between' }}>
              <span>AI Content Generations</span>
              <span style={{ color: 'hsl(var(--text-primary))' }}>{currentGenerations} / {maxGenerations === 999999 ? 'Unlimited' : maxGenerations}</span>
            </h3>
            <div style={{ width: '100%', height: '8px', background: 'hsl(var(--border-muted))', borderRadius: '99px', overflow: 'hidden', marginBottom: '0.75rem' }}>
              <div style={{ width: `${maxGenerations === 999999 ? 0 : gensPercent}%`, height: '100%', background: 'linear-gradient(90deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', borderRadius: '99px' }} />
            </div>
            <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-dim))' }}>
              Generations and script regenerations consumed in the current calendar month.
            </p>
          </Card>
        </section>

        {/* Pricing Plan Grid */}
        <section style={{ marginBottom: '3.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>Available Subscription Plans</h2>
          <div className="bento-grid">
            {plans.map((p) => {
              const isCurrent = p.name === activePlanName;
              return (
                <Card 
                  key={p.id} 
                  style={{ 
                    padding: '2.5rem', 
                    border: isCurrent ? '2px solid hsl(var(--accent-primary))' : '1px solid hsl(var(--border-muted))',
                    position: 'relative'
                  }}
                >
                  {isCurrent && (
                    <Badge status="Active Plan" style={{ position: 'absolute', top: '1rem', right: '1rem' }} />
                  )}
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>{p.name}</h3>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem', marginBottom: '1.5rem' }}>
                    <span style={{ fontSize: '2.25rem', fontWeight: 800 }}>₹{parseInt(p.price_monthly)}</span>
                    <span style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem' }}>/ mo</span>
                  </div>

                  <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem 0', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem', color: 'hsl(var(--text-muted))' }}>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <CheckCircle2 size={16} color="hsl(var(--success))" /> 
                      {p.max_projects === 999999 ? 'Unlimited Projects' : `${p.max_projects} Projects Limit`}
                    </li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <CheckCircle2 size={16} color="hsl(var(--success))" /> 
                      {p.max_generations_per_month === 999999 ? 'Unlimited AI Content Generations' : `${p.max_generations_per_month} Generations/month`}
                    </li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <CheckCircle2 size={16} color="hsl(var(--success))" /> 
                      18% GST Compliant legal invoices
                    </li>
                  </ul>

                  <Button 
                    onClick={() => handleCheckout(p)} 
                    disabled={isCurrent || submitting}
                    variant={isCurrent ? 'secondary' : 'primary'}
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    {isCurrent ? 'Current Plan' : 'Select Plan'}
                    {!isCurrent && <ArrowRight size={16} />}
                  </Button>
                </Card>
              );
            })}
          </div>
          {activePlanName !== 'Free Trial' && subStatus === 'ACTIVE' && (
            <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
              <Button onClick={handleCancelSubscription} variant="danger" className="secondary" disabled={submitting}>
                Cancel Active Subscription
              </Button>
            </div>
          )}
        </section>

        {/* GST Form & Payments History */}
        <section className="bento-grid" style={{ marginBottom: '3rem' }}>
          {/* GST Details Form */}
          <Card style={{ padding: '2.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '1.25rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Receipt size={20} color="hsl(var(--accent-primary))" />
              Indian GST & Invoicing Info
            </h2>
            <form onSubmit={handleUpdateGSTDetails} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <Input 
                label="Registered Legal Entity Name"
                placeholder="e.g. Acme Social Technologies Pvt Ltd"
                value={legalName}
                onChange={e => setLegalName(e.target.value)}
              />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <Input 
                  label="GSTIN ID"
                  placeholder="e.g. 29AAAAA1111A1Z1"
                  value={gstin}
                  onChange={e => setGstin(e.target.value)}
                  maxLength={15}
                />
                <Input 
                  label="Contact Mobile"
                  placeholder="e.g. 9876543210"
                  value={billingContact}
                  onChange={e => setBillingContact(e.target.value)}
                />
              </div>
              <Input 
                label="Billing Contact Email"
                type="email"
                placeholder="billing@company.com"
                value={billingEmail}
                onChange={e => setBillingEmail(e.target.value)}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Billing Address</label>
                <textarea 
                  rows={3}
                  placeholder="Full physical address for structured invoice generation"
                  value={billingAddress}
                  onChange={e => setBillingAddress(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
              <Button type="submit" disabled={submitting} style={{ marginTop: '0.5rem', justifyContent: 'center' }}>
                Update Invoice Details
              </Button>
            </form>
          </Card>

          {/* Invoice/Payment Records */}
          <Card style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <FileText size={20} color="hsl(var(--accent-primary))" />
              Invoices & Billing History
            </h2>
            <div style={{ flex: 1, overflowY: 'auto', maxHeight: '350px' }}>
              {!history || !history.invoices || !Array.isArray(history.invoices) || history.invoices.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'hsl(var(--text-dim))', padding: '3rem 0' }}>
                  No payment invoices generated yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {history.invoices.map((inv) => (
                    <div 
                      key={inv.id}
                      style={{ 
                        border: '1px solid hsl(var(--border-muted))', 
                        borderRadius: '10px', 
                        padding: '1rem', 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{inv.invoice_number}</div>
                        <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))', marginTop: '0.2rem' }}>
                          {new Date(inv.created_at).toLocaleDateString()} &bull; GSTIN: {inv.gstin || 'Individual'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>₹{parseInt(inv.amount)}</span>
                        <Button 
                          onClick={() => downloadInvoice(inv)}
                          variant="secondary"
                          style={{ padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
                        >
                          Invoice PDF
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </section>

        {/* Policies and Terms Placeholders */}
        <footer style={{ borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '2rem', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.5rem', fontSize: '0.85rem', color: 'hsl(var(--text-dim))' }}>
          <div>
            &copy; 2026 ViralOps. Low PCI Scope Compliant System.
          </div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <a href="/terms" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>Terms of Service</a>
            <a href="/privacy" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>Privacy Policy</a>
            <a href="/refund" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>Refund and Cancellation</a>
          </div>
        </footer>

        {/* Offline Sandbox Payment Simulation Overlay Modal */}
        {mockCheckoutData && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
            <Card style={{ maxWidth: '440px', width: '100%', padding: '2.5rem', border: '1px solid hsl(var(--warning) / 0.5)' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'hsl(var(--warning))', display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1rem' }}>
                <AlertTriangle size={24} />
                Sandbox Payment Simulation
              </h2>
              <p style={{ fontSize: '0.9rem', color: 'hsl(var(--text-muted))', lineHeight: 1.6, marginBottom: '1.5rem' }}>
                You are executing locally offline, or active Razorpay API Keys are not configured. We can simulate a successful Razorpay gateway callback for testing:
              </p>
              <div style={{ background: 'hsl(var(--border-muted) / 0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.85rem', color: 'hsl(var(--text-primary))', display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '2rem' }}>
                <div><strong>Mock Subscription ID:</strong> {mockCheckoutData.subscription_id}</div>
                <div><strong>Simulation Rate:</strong> ₹{mockCheckoutData.amount} INR</div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <Button 
                  onClick={handleSimulateMockPayment}
                  style={{ flex: 1, justifyContent: 'center' }}
                  disabled={submitting}
                >
                  Confirm Success Mock Payment
                </Button>
                <Button 
                  variant="secondary"
                  onClick={() => setMockCheckoutData(null)}
                  style={{ justifyContent: 'center' }}
                  disabled={submitting}
                >
                  Cancel
                </Button>
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
