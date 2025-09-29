"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Document } from "@/lib/stores/document-store"

interface FinancialFactsProps {
  document: Document
}

export function FinancialFacts({ document }: FinancialFactsProps) {
  const { financial_facts, investment_data, key_metrics } = document

  if (!financial_facts && !investment_data && !key_metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Financial Facts</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            No financial facts extracted yet. This information will be available once document processing is complete.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Facts</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {financial_facts?.revenue && (
          <div>
            <h4 className="font-medium mb-3">Revenue:</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Current Year:</span>
                <div className="font-medium">{financial_facts.revenue.current_year || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Previous Year:</span>
                <div className="font-medium">{financial_facts.revenue.previous_year || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Currency:</span>
                <div className="font-medium">{financial_facts.revenue.currency || "USD"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Period:</span>
                <div className="font-medium">{financial_facts.revenue.period || "Annual"}</div>
              </div>
            </div>
          </div>
        )}

        {financial_facts?.profit_loss && (
          <div>
            <h4 className="font-medium mb-3">Profit & Loss:</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Net Income:</span>
                <div className="font-medium">{financial_facts.profit_loss.net_income || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Gross Profit:</span>
                <div className="font-medium">{financial_facts.profit_loss.gross_profit || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Operating Profit:</span>
                <div className="font-medium">{financial_facts.profit_loss.operating_profit || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Currency:</span>
                <div className="font-medium">{financial_facts.profit_loss.currency || "USD"}</div>
              </div>
            </div>
          </div>
        )}

        {investment_data && (
          <div>
            <h4 className="font-medium mb-3">Investment Data:</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Sector:</span>
                <div className="font-medium">{investment_data.sector || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Stage:</span>
                <div className="font-medium">{investment_data.stage || "N/A"}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Market Cap:</span>
                <div className="font-medium">{investment_data.market_cap || investment_data.valuation || "N/A"}</div>
              </div>
            </div>
          </div>
        )}

        {key_metrics && (
          <div>
            <h4 className="font-medium mb-3">Key Metrics:</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {key_metrics.ev_sales_ttm && (
                <div>
                  <span className="text-muted-foreground">EV/Sales (TTM):</span>
                  <div className="font-medium">{key_metrics.ev_sales_ttm}</div>
                </div>
              )}
              {key_metrics.five_year_median && (
                <div>
                  <span className="text-muted-foreground">5-Year Median:</span>
                  <div className="font-medium">{key_metrics.five_year_median}</div>
                </div>
              )}
              {key_metrics.five_year_high && (
                <div>
                  <span className="text-muted-foreground">5-Year High:</span>
                  <div className="font-medium">{key_metrics.five_year_high}</div>
                </div>
              )}
              {key_metrics.five_year_low && (
                <div>
                  <span className="text-muted-foreground">5-Year Low:</span>
                  <div className="font-medium">{key_metrics.five_year_low}</div>
                </div>
              )}
              {key_metrics.customer_count && (
                <div>
                  <span className="text-muted-foreground">Customer Count:</span>
                  <div className="font-medium">{key_metrics.customer_count.toLocaleString()}</div>
                </div>
              )}
              {key_metrics.arr && (
                <div>
                  <span className="text-muted-foreground">ARR:</span>
                  <div className="font-medium">{key_metrics.arr}</div>
                </div>
              )}
              {key_metrics.churn_rate && (
                <div>
                  <span className="text-muted-foreground">Churn Rate:</span>
                  <div className="font-medium">{key_metrics.churn_rate}</div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
