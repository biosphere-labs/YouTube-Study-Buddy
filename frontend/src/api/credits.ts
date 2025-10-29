import apiClient from './client';
import type { CreditBalance, CreditTransaction, UsageStats } from '@/types';

export interface PurchaseCreditsRequest {
  amount: number;
  paymentMethodId: string;
}

export interface ListTransactionsResponse {
  transactions: CreditTransaction[];
  nextToken?: string;
}

export const creditsApi = {
  // Get credit balance
  getBalance: async (): Promise<CreditBalance> => {
    const response = await apiClient.get<CreditBalance>('/credits/balance');
    return response.data;
  },

  // Get credit transaction history with pagination support
  getTransactions: async (limit: number = 50, nextToken?: string): Promise<ListTransactionsResponse> => {
    const params: Record<string, string | number> = { limit };
    if (nextToken) {
      params.nextToken = nextToken;
    }
    const response = await apiClient.get<ListTransactionsResponse>('/credits/transactions', { params });
    return response.data;
  },

  // Purchase credits via Stripe
  purchaseCredits: async (data: PurchaseCreditsRequest): Promise<CreditTransaction> => {
    const response = await apiClient.post<CreditTransaction>('/credits/purchase', data);
    return response.data;
  },

  // Get usage statistics
  getUsageStats: async (): Promise<UsageStats> => {
    const response = await apiClient.get<UsageStats>('/credits/usage');
    return response.data;
  },
};
