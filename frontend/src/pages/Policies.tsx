import React from 'react';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { Sparkles, ArrowLeft } from 'lucide-react';

interface PoliciesProps {
  page: 'terms' | 'privacy' | 'refund';
}

export default function Policies({ page }: PoliciesProps) {
  const getPolicyContent = () => {
    switch (page) {
      case 'terms':
        return {
          title: 'Terms of Service',
          lastUpdated: 'May 2026',
          sections: [
            {
              heading: '1. Acceptance of Terms',
              content: 'By accessing or using the ViralOps platform, you agree to comply with and be bound by these Terms of Service. If you do not agree to these terms, you must immediately terminate usage of the services.'
            },
            {
              heading: '2. User Accounts & Workspaces',
              content: 'You are responsible for safeguarding your credentials, configuring multi-tenant permissions, and ensuring that all project inputs, YouTube video uploads, or files belong to or are authorized for your use. Account sharing outside of team membership parameters is strictly prohibited.'
            },
            {
              heading: '3. Subscription Fees & Quota Enforcements',
              content: 'Fees are billed in advance in Indian Rupees (INR) using compliant gateways. Workspace limits (projects, AI credits/generations count) are strictly checked and enforced based on your subscription tier.'
            },
            {
              heading: '4. Limitation of Liability',
              content: 'ViralOps does not warrant that AI-generated hooks, titles, transcripts, or caption outputs are free from trademark/copyright conflicts. Users are solely responsible for verifying compliance before publication.'
            }
          ]
        };
      case 'privacy':
        return {
          title: 'Privacy Policy',
          lastUpdated: 'May 2026',
          sections: [
            {
              heading: '1. Information We Collect',
              content: 'We collect your username, email address, password hashes, and workspace configurations. For billing compliance, we store company legal name, address details, and GSTIN numbers. Card numbers and security details are stored directly on Razorpay\'s secure servers (Low PCI scope).'
            },
            {
              heading: '2. Ingestion Files & AI Inputs',
              content: 'Video, audio, YouTube URLs, and text content uploaded to ViralOps are processed through our AI transcription and generation pipelines. We do not sell or distribute your raw asset data to third parties.'
            },
            {
              heading: '3. Cookie Policy',
              content: 'We use secure cookies to store authentication tokens (SimpleJWT) and track session states. Disabling cookies will terminate your access to dashboard features.'
            }
          ]
        };
      case 'refund':
        return {
          title: 'Refund & Cancellation Policy',
          lastUpdated: 'May 2026',
          sections: [
            {
              heading: '1. Cancellations',
              content: 'Subscriptions can be cancelled at any time from your Workspace Billing dashboard. Once cancelled, your workspace status transitions to CANCELLED, and your limits revert to standard Free Trial quotas at the end of the current billing cycle.'
            },
            {
              heading: '2. Refunds',
              content: 'Due to the operational costs associated with AI credits and transcription pipelines, subscription fees are non-refundable. If you believe you were charged in error, please submit an appeal containing your Razorpay Payment ID to support@viralops.com within 7 days of the charge.'
            }
          ]
        };
      default:
        return { title: 'Legal Policies', lastUpdated: '', sections: [] };
    }
  };

  const { title, lastUpdated, sections } = getPolicyContent();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))', padding: '2rem' }}>
      <div style={{ maxWidth: '720px', width: '100%', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Header Branding */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Sparkles size={24} color="hsl(var(--accent-primary))" />
            <span style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>
              Viral<span style={{ color: 'hsl(var(--accent-primary))' }}>Ops</span>
            </span>
          </div>
          <Button variant="secondary" onClick={() => window.close()} style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}>
            <ArrowLeft size={16} /> Close Tab
          </Button>
        </div>

        {/* Content Card */}
        <Card style={{ padding: '3rem' }}>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>{title}</h1>
          <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.9rem', marginBottom: '2.5rem' }}>
            Last Updated: {lastUpdated}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', lineHeight: 1.7, color: 'hsl(var(--text-muted))' }}>
            {sections.map((sec, idx) => (
              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <h3 style={{ color: 'hsl(var(--text-primary))', fontSize: '1.15rem', fontWeight: 700 }}>
                  {sec.heading}
                </h3>
                <p style={{ fontSize: '0.95rem' }}>{sec.content}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Footer info */}
        <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'hsl(var(--text-dim))' }}>
          ViralOps India B2B Compliant Legal Policies.
        </div>
      </div>
    </div>
  );
}
