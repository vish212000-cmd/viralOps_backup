export interface Plan {
  id: number;
  name: 'FREE' | 'PRO' | 'TEAMS' | 'ENTERPRISE';
  price_monthly: string;
  price_yearly: string;
  max_projects: number;
  max_generations: number;
  ai_brand_tone: boolean;
  custom_domain: boolean;
}

export interface Usage {
  projects: number;
  generations: number;
  limit_projects: number;
  limit_generations: number;
  storage_gb_used?: number;
}

export interface Subscription {
  id: number;
  plan: Plan;
  status: 'ACTIVE' | 'PAST_DUE' | 'CANCELLED' | 'PENDING';
  current_period_end: string | null;
  razorpay_customer_id: string;
  legal_name: string;
  billing_contact: string;
  billing_email: string;
  billing_address: string;
  gstin: string;
  usage?: Usage;
}

export interface PaymentRecord {
  id: number;
  razorpay_payment_id: string;
  amount: string;
  currency: string;
  status: string;
  created_at: string;
}

export interface InvoiceRecord {
  id: number;
  invoice_number: string;
  amount: string;
  tax_amount: string;
  gstin: string;
  legal_name: string;
  billing_address: string;
  created_at: string;
}

