import { api } from '../utils/api';
import { Plan, Subscription } from '../types/billing';

export interface OrderResponse {
  order_id: string;
  amount: number;
  currency: string;
}

export const billingApi = {
  getPlans: async (): Promise<Plan[]> => {
    return api.get('/api/billing/plans/');
  },

  getMySubscription: async (): Promise<Subscription> => {
    return api.get('/api/billing/subscription/');
  },

  createSubscription: async (planId: number | string): Promise<OrderResponse> => {
    return api.post('/api/billing/subscription/', { plan_id: planId });
  },

  verifyPayment: async (
    orderId: string,
    paymentId: string,
    signature: string,
    planId?: number | string
  ): Promise<any> => {
    return api.post('/api/billing/subscription/verify/', {
      order_id: orderId,
      payment_id: paymentId,
      signature: signature,
      plan_id: planId,
    });
  },

  cancelSubscription: async (reason: string): Promise<any> => {
    return api.post('/api/billing/subscription/cancel/', { reason });
  },

  updateDetails: async (details: {
    legal_name: string;
    billing_contact: string;
    billing_email: string;
    billing_address: string;
    gstin: string;
  }): Promise<Subscription> => {
    return api.post('/api/billing/subscription/update-details/', details);
  },

  getHistory: async (): Promise<{ payments: any[]; invoices: any[] }> => {
    return api.get('/api/billing/subscription/history/');
  },
};
