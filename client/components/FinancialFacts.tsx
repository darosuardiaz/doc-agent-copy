'use client';

interface FinancialValue {
  current_year?: number | null;
  previous_year?: number | null;
  net_income?: number | null;
  gross_profit?: number | null;
  operating_profit?: number | null;
  operating_cash_flow?: number | null;
  free_cash_flow?: number | null;
  total_debt?: number | null;
  equity?: number | null;
  debt_to_equity_ratio?: number | null;
  ebitda?: number | null;
  margin_percentage?: number | null;
  growth_rate?: number | null;
  currency?: string;
  period?: string;
}

interface FinancialFactsProps {
  financialFacts: {
    revenue?: FinancialValue;
    profit_loss?: FinancialValue;
    cash_flow?: FinancialValue;
    debt_equity?: FinancialValue;
    other_metrics?: FinancialValue;
  };
}

function formatCurrency(value: number | null | undefined, currency: string = 'USD'): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency === 'null' ? 'USD' : currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  
  return value.toLocaleString();
}

function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  
  return `${value.toFixed(1)}%`;
}

function formatValue(value: any): string {
  if (value === null || value === undefined || value === '' || value === 'null') {
    return 'N/A';
  }
  
  if (typeof value === 'string') {
    return value;
  }
  
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  
  return String(value);
}

export default function FinancialFacts({ financialFacts }: FinancialFactsProps) {
  if (!financialFacts || Object.keys(financialFacts).length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Financial Facts</h2>
      
      <div className="grid gap-6">
        {/* Revenue Section */}
        {financialFacts.revenue && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Revenue:</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">Current Year:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.revenue.current_year, financialFacts.revenue.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Previous Year:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.revenue.previous_year, financialFacts.revenue.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Currency:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(financialFacts.revenue.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Period:</span>
                <p className="font-medium text-gray-900 capitalize">
                  {formatValue(financialFacts.revenue.period)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Profit & Loss Section */}
        {financialFacts.profit_loss && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Profit & Loss:</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">Net Income:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.profit_loss.net_income, financialFacts.profit_loss.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Gross Profit:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.profit_loss.gross_profit, financialFacts.profit_loss.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Operating Profit:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.profit_loss.operating_profit, financialFacts.profit_loss.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Currency:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(financialFacts.profit_loss.currency)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Cash Flow Section */}
        {financialFacts.cash_flow && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Cash Flow:</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">Operating Cash Flow:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.cash_flow.operating_cash_flow, financialFacts.cash_flow.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Free Cash Flow:</span>
                <p className="font-medium text-gray-900">
                  {formatCurrency(financialFacts.cash_flow.free_cash_flow, financialFacts.cash_flow.currency)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Currency:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(financialFacts.cash_flow.currency)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Debt & Equity Section */}
        {financialFacts.debt_equity && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Debt & Equity:</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">Total Debt:</span>
                <p className="font-medium text-gray-900">
                  {formatNumber(financialFacts.debt_equity.total_debt)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Equity:</span>
                <p className="font-medium text-gray-900">
                  {formatNumber(financialFacts.debt_equity.equity)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Debt-to-Equity Ratio:</span>
                <p className="font-medium text-gray-900">
                  {formatNumber(financialFacts.debt_equity.debt_to_equity_ratio)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Other Metrics Section */}
        {financialFacts.other_metrics && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Other Metrics:</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">EBITDA:</span>
                <p className="font-medium text-gray-900">
                  {formatNumber(financialFacts.other_metrics.ebitda)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Margin Percentage:</span>
                <p className="font-medium text-gray-900">
                  {formatPercentage(financialFacts.other_metrics.margin_percentage)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Growth Rate:</span>
                <p className="font-medium text-gray-900">
                  {formatPercentage(financialFacts.other_metrics.growth_rate)}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}