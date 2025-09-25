'use client';

interface InvestmentDataProps {
  investmentData: {
    investment_highlights?: string[];
    risk_factors?: string[];
    market_opportunity?: {
      market_size?: number | null;
      growth_rate?: number | null;
      competitive_position?: string | null;
    };
    business_model?: {
      type?: string | null;
      revenue_streams?: string[];
      key_customers?: string[];
    };
    strategic_initiatives?: string[];
    exit_strategy?: {
      timeline?: string | null;
      target_multiple?: number | null;
      potential_buyers?: string[];
    };
  };
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

function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  
  return `${value.toFixed(1)}%`;
}

function formatList(items: string[] | undefined): React.ReactNode {
  if (!items || items.length === 0) {
    return <span className="text-gray-500 italic">None specified</span>;
  }
  
  return (
    <ul className="list-disc list-inside space-y-1">
      {items.map((item, index) => (
        <li key={index} className="text-sm text-gray-700">{item}</li>
      ))}
    </ul>
  );
}

export default function InvestmentData({ investmentData }: InvestmentDataProps) {
  if (!investmentData || Object.keys(investmentData).length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Investment Data</h2>
      
      <div className="grid gap-6">
        {/* Investment Highlights */}
        {investmentData.investment_highlights && investmentData.investment_highlights.length > 0 && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Investment Highlights:</h3>
            <div className="ml-4">
              {formatList(investmentData.investment_highlights)}
            </div>
          </div>
        )}

        {/* Risk Factors */}
        {investmentData.risk_factors && investmentData.risk_factors.length > 0 && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Risk Factors:</h3>
            <div className="ml-4">
              {formatList(investmentData.risk_factors)}
            </div>
          </div>
        )}

        {/* Market Opportunity */}
        {investmentData.market_opportunity && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Market Opportunity:</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 ml-4">
              <div>
                <span className="text-gray-600 text-sm">Market Size:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(investmentData.market_opportunity.market_size)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Growth Rate:</span>
                <p className="font-medium text-gray-900">
                  {formatPercentage(investmentData.market_opportunity.growth_rate)}
                </p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Competitive Position:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(investmentData.market_opportunity.competitive_position)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Business Model */}
        {investmentData.business_model && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Business Model:</h3>
            <div className="ml-4 space-y-4">
              <div>
                <span className="text-gray-600 text-sm">Type:</span>
                <p className="font-medium text-gray-900">
                  {formatValue(investmentData.business_model.type)}
                </p>
              </div>
              
              {investmentData.business_model.revenue_streams && investmentData.business_model.revenue_streams.length > 0 && (
                <div>
                  <span className="text-gray-600 text-sm block mb-2">Revenue Streams:</span>
                  {formatList(investmentData.business_model.revenue_streams)}
                </div>
              )}
              
              {investmentData.business_model.key_customers && investmentData.business_model.key_customers.length > 0 && (
                <div>
                  <span className="text-gray-600 text-sm block mb-2">Key Customers:</span>
                  {formatList(investmentData.business_model.key_customers)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Strategic Initiatives */}
        {investmentData.strategic_initiatives && investmentData.strategic_initiatives.length > 0 && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Strategic Initiatives:</h3>
            <div className="ml-4">
              {formatList(investmentData.strategic_initiatives)}
            </div>
          </div>
        )}

        {/* Exit Strategy */}
        {investmentData.exit_strategy && (
          <div>
            <h3 className="text-base font-medium text-gray-900 mb-3">Exit Strategy:</h3>
            <div className="ml-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-600 text-sm">Timeline:</span>
                  <p className="font-medium text-gray-900">
                    {formatValue(investmentData.exit_strategy.timeline)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600 text-sm">Target Multiple:</span>
                  <p className="font-medium text-gray-900">
                    {formatValue(investmentData.exit_strategy.target_multiple)}
                  </p>
                </div>
              </div>
              
              {investmentData.exit_strategy.potential_buyers && investmentData.exit_strategy.potential_buyers.length > 0 && (
                <div>
                  <span className="text-gray-600 text-sm block mb-2">Potential Buyers:</span>
                  {formatList(investmentData.exit_strategy.potential_buyers)}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}