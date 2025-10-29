import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

interface PurchaseModalProps {
  open: boolean;
  onClose: () => void;
}

const creditPackages = [
  { amount: 10, price: 4.99, popular: false },
  { amount: 25, price: 9.99, popular: true },
  { amount: 50, price: 17.99, popular: false },
  { amount: 100, price: 29.99, popular: false },
];

export function PurchaseModal({ open, onClose }: PurchaseModalProps) {
  const [selectedPackage, setSelectedPackage] = useState(creditPackages[1]);

  if (!open) return null;

  const handlePurchase = () => {
    // TODO: Integrate with Stripe payment
    alert(`Purchase ${selectedPackage.amount} credits for $${selectedPackage.price}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="max-w-2xl w-full mx-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Purchase Credits</CardTitle>
              <CardDescription>
                Choose a credit package to continue using YouTube Study Buddy
              </CardDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              {creditPackages.map((pkg) => (
                <div
                  key={pkg.amount}
                  onClick={() => setSelectedPackage(pkg)}
                  className={`relative p-6 border-2 rounded-lg cursor-pointer transition-all ${
                    selectedPackage.amount === pkg.amount
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {pkg.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                        Most Popular
                      </span>
                    </div>
                  )}
                  <div className="text-center">
                    <div className="text-3xl font-bold">{pkg.amount}</div>
                    <div className="text-sm text-muted-foreground mb-2">Credits</div>
                    <div className="text-2xl font-bold text-primary">${pkg.price}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      ${(pkg.price / pkg.amount).toFixed(2)} per credit
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Button className="w-full" size="lg" onClick={handlePurchase}>
                Purchase {selectedPackage.amount} Credits for ${selectedPackage.price}
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                Secure payment powered by Stripe
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
