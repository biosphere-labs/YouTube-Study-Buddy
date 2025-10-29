import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { creditsApi, type PurchaseCreditsRequest } from '@/api/credits';

export function useCredits() {
  const queryClient = useQueryClient();

  const { data: balance, isLoading: isLoadingBalance } = useQuery({
    queryKey: ['creditBalance'],
    queryFn: creditsApi.getBalance,
  });

  const { data: transactionsData, isLoading: isLoadingTransactions } = useQuery({
    queryKey: ['creditTransactions'],
    queryFn: () => creditsApi.getTransactions(),
  });

  const transactions = transactionsData?.transactions || [];

  const { data: usageStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['usageStats'],
    queryFn: creditsApi.getUsageStats,
  });

  const purchaseMutation = useMutation({
    mutationFn: (data: PurchaseCreditsRequest) => creditsApi.purchaseCredits(data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['creditBalance'] });
      queryClient.invalidateQueries({ queryKey: ['creditTransactions'] });
    },
  });

  return {
    balance,
    transactions,
    usageStats,
    isLoading: isLoadingBalance || isLoadingTransactions || isLoadingStats,
    purchaseCredits: purchaseMutation.mutate,
    isPurchasing: purchaseMutation.isPending,
  };
}
