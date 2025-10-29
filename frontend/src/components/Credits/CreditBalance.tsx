import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useCredits } from '@/hooks/useCredits';
import { CreditCard, Plus } from 'lucide-react';
import { useState } from 'react';
import { PurchaseModal } from './PurchaseModal';

export function CreditBalance() {
  const { balance, isLoading } = useCredits();
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Credit Balance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle>Credit Balance</CardTitle>
          <CreditCard className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-4xl font-bold">{balance?.balance || 0}</div>
          <p className="text-xs text-muted-foreground mt-2">
            Total earned: {balance?.totalEarned || 0} | Total spent:{' '}
            {balance?.totalSpent || 0}
          </p>
          <Button
            className="w-full mt-4"
            onClick={() => setIsPurchaseModalOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Purchase Credits
          </Button>
        </CardContent>
      </Card>

      <PurchaseModal
        open={isPurchaseModalOpen}
        onClose={() => setIsPurchaseModalOpen(false)}
      />
    </>
  );
}
