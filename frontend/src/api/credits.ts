import apiClient from './client';
import type { CreditBalance, CreditTransaction, UsageStats } from '@/types';

export interface PurchaseCreditsRequest {
  amount: number;
  paymentMethodId: string;
}

export const creditsApi = {
  // Get credit balance
  getBalance: async (): Promise<CreditBalance> => {
    const response = await apiClient.get<CreditBalance>('/credits/balance');
    return response.data;
  },

  // Get credit transaction history
  getTransactions: async (): Promise<CreditTransaction[]> => {
    const response = await apiClient.get<CreditTransaction[]>('/credits/transactions');
    return response.data;
  },

  // Purchase credits
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
