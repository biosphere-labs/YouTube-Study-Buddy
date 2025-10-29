import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCredits } from '@/hooks/useCredits';
import { ArrowDownCircle, ArrowUpCircle, Loader2 } from 'lucide-react';
import type { CreditTransaction } from '@/types';

export function TransactionHistory() {
  const { transactions, isLoading } = useCredits();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const getTransactionIcon = (type: CreditTransaction['type']) => {
    switch (type) {
      case 'purchase':
      case 'refund':
        return <ArrowUpCircle className="h-5 w-5 text-green-500" />;
      case 'video_processing':
        return <ArrowDownCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const formatAmount = (transaction: CreditTransaction) => {
    const sign = transaction.amount > 0 ? '+' : '';
    return `${sign}${transaction.amount}`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction History</CardTitle>
      </CardHeader>
      <CardContent>
        {transactions && transactions.length > 0 ? (
          <div className="space-y-3">
            {transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  {getTransactionIcon(transaction.type)}
                  <div>
                    <p className="font-medium text-sm">{transaction.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(transaction.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div
                  className={`font-semibold ${
                    transaction.amount > 0
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {formatAmount(transaction)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-8">
            No transactions yet
          </p>
        )}
      </CardContent>
    </Card>
  );
}
