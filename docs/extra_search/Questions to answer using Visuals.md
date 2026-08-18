# Business Questions for Each Grain/Fact Table

Here's a comprehensive set of business questions organized by fact table, designed for PowerBI dashboards and visualizations:

---

## FACT 1: fact_lineitem (Line Item Grain)
**🎯 Purpose:** Detailed sales analysis, operational efficiency, and product performance

### Category 1: Sales Performance & Revenue Analysis

```powerbi
/*
DASHBOARD: Sales Performance Dashboard
*/

-- 1. Revenue Trends
Q1: "What is the daily, weekly, and monthly revenue trend over time?"
Visual: Line chart with date hierarchy (Year → Quarter → Month → Day)
Measures: SUM(extended_price * (1 - discount) * (1 + tax))
Dimensions: dim_date (full_date, year, month)

-- 2. Top Performing Products
Q2: "Which products generate the highest revenue and quantity sold?"
Visual: Bar chart (Top 20 products)
Measures: SUM(revenue), SUM(quantity)
Dimensions: dim_part (product_name, brand, type)

-- 3. Revenue by Market Segment
Q3: "How do different customer market segments contribute to revenue?"
Visual: Donut chart or stacked bar
Measures: SUM(revenue)
Dimensions: dim_customer (market_segment)

-- 4. Regional Revenue Distribution
Q4: "Which regions and nations generate the most revenue?"
Visual: Map visualization (geographic heat map)
Measures: SUM(revenue)
Dimensions: dim_customer (region_name, nation_name)

-- 5. Time-based Revenue Patterns
Q5: "Are there seasonal patterns or peak sales periods?"
Visual: Calendar heatmap or time series decomposition
Measures: SUM(revenue)
Dimensions: dim_date (month, day_of_week, is_weekend)
```

### Category 2: Discount & Pricing Strategy

```powerbi
/*
DASHBOARD: Pricing & Discount Analytics
*/

-- 6. Discount Impact Analysis
Q6: "How does discount percentage correlate with sales volume?"
Visual: Scatter plot (discount % vs quantity sold)
Measures: AVG(discount), SUM(quantity), SUM(revenue)
Dimensions: dim_part (brand, type)

-- 7. Discount Distribution
Q7: "What is the distribution of discounts applied across orders?"
Visual: Histogram with discount buckets (0-5%, 5-10%, 10-15%, etc.)
Measures: COUNT(line items), SUM(revenue)
Dimensions: discount brackets

-- 8. Profit Margin by Product Category
Q8: "Which product categories have the highest profit margins after discounts?"
Visual: Treemap or bar chart
Measures: (revenue - cost) / revenue as margin
Dimensions: dim_part (category, brand)

-- 9. Bulk Purchase Patterns
Q9: "Do higher quantity purchases receive higher discounts?"
Visual: Scatter plot (quantity vs discount)
Measures: AVG(quantity), AVG(discount)
Dimensions: dim_part (type)

-- 10. Discount Effectiveness
Q10: "What is the revenue lift from discounted vs non-discounted items?"
Visual: Side-by-side bar chart
Measures: SUM(revenue), COUNT(line items)
Filter: discount = 0 vs discount > 0
```

### Category 3: Operational & Shipping Efficiency

```powerbi
/*
DASHBOARD: Shipping & Operations Dashboard
*/

-- 11. Shipping Mode Performance
Q11: "Which shipping modes are most commonly used and what's their cost efficiency?"
Visual: Bar chart + line combo
Measures: COUNT(line items), AVG(quantity), AVG(cost_per_unit)
Dimensions: dim_shipping (ship_mode, carrier)

-- 12. Shipping Instructions Analysis
Q12: "What are the most common shipping instructions by region?"
Visual: Stacked bar chart
Measures: COUNT(line items)
Dimensions: dim_shipping (ship_instruct), dim_customer (region_name)

-- 13. Ship Date vs Commit Date Analysis
Q13: "What percentage of shipments are delayed vs on-time?"
Visual: Gauge chart + trend line
Measures: COUNT(CASE WHEN ship_date > commit_date THEN 1 END) / COUNT(*)
Dimensions: dim_date (year, month)

-- 14. Return Flag Analysis
Q14: "Which products and regions have the highest return rates?"
Visual: Heat map or bar chart
Measures: COUNT(CASE WHEN return_flag = 'R' THEN 1 END) / COUNT(*)
Dimensions: dim_part (brand, type), dim_customer (region_name)

-- 15. Shipping Cost Optimization
Q15: "How does shipping cost per unit vary by product type and region?"
Visual: Matrix or heatmap
Measures: AVG(cost_per_unit)
Dimensions: dim_part (type), dim_customer (region_name)
```

### Category 4: Product & Supplier Analysis

```powerbi
/*
DASHBOARD: Product & Supplier Performance
*/

-- 16. Supplier Performance Ranking
Q16: "Which suppliers provide the highest quality products (based on returns and discounts)?"
Visual: Performance scorecard
Measures: SUM(revenue), AVG(discount), return_rate
Dimensions: dim_supplier (supplier_name, region_name)

-- 17. Product Category Performance
Q17: "How do different product categories perform across seasons?"
Visual: Line chart with category breakdown
Measures: SUM(revenue)
Dimensions: dim_part (type, brand), dim_date (quarter, month)

-- 18. Price Point Analysis
Q18: "What is the optimal price range for different product types?"
Visual: Scatter plot (price vs quantity sold)
Measures: AVG(retail_price), SUM(quantity)
Dimensions: dim_part (type, size)

-- 19. Product Size & Container Analysis
Q19: "Which product sizes and containers are most popular by region?"
Visual: Heatmap or matrix
Measures: SUM(quantity)
Dimensions: dim_part (size, container), dim_customer (region_name)

-- 20. Brand Loyalty Analysis
Q20: "Which brands have the highest customer repeat purchase rate?"
Visual: Bar chart
Measures: COUNT(DISTINCT customer_key) per brand
Dimensions: dim_part (brand)
```

---

## FACT 2: fact_orders (Order Grain)
**🎯 Purpose:** Order fulfillment, customer behavior, and operational efficiency

### Category 1: Order Volume & Value Analysis

```powerbi
/*
DASHBOARD: Order Analytics Dashboard
*/

-- 21. Order Volume Trends
Q21: "What is the daily, weekly, and monthly order volume trend?"
Visual: Area chart with time hierarchy
Measures: COUNT(order_key), SUM(total_amount)
Dimensions: dim_date (full_date, year, month)

-- 22. Average Order Value (AOV) Analysis
Q22: "How does average order value vary by customer segment and region?"
Visual: Bar chart with segmentation
Measures: AVG(total_amount)
Dimensions: dim_customer (market_segment, region_name)

-- 23. Order Size Distribution
Q23: "What is the distribution of order sizes (number of items per order)?"
Visual: Histogram
Measures: COUNT(order_key) by total_quantity buckets
Dimensions: total_quantity ranges (1-5, 6-10, 11-20, 21+)

-- 24. Customer Order Frequency
Q24: "How frequently do customers place orders (daily, weekly, monthly)?"
Visual: Distribution chart
Measures: AVG(days_between_orders)
Dimensions: dim_customer (market_segment)

-- 25. Order Value by Clerk Performance
Q25: "Which clerks process the highest value orders?"
Visual: Bar chart (Top 20 clerks)
Measures: SUM(total_amount), COUNT(order_key), AVG(total_amount)
Dimensions: clerk
```

### Category 2: Order Status & Fulfillment

```powerbi
/*
DASHBOARD: Order Fulfillment Dashboard
*/

-- 26. Order Status Distribution
Q26: "What is the current status distribution of all orders?"
Visual: Donut chart or funnel
Measures: COUNT(order_key)
Dimensions: dim_order_status (status_name, is_complete)

-- 27. Fulfillment Cycle Time
Q27: "What is the average time from order to fulfillment?"
Visual: Line chart over time
Measures: AVG(days_to_complete)
Dimensions: dim_date (order_date_key), dim_order_status

-- 28. Order Priority Analysis
Q28: "How does order priority affect fulfillment time and customer satisfaction?"
Visual: Box plot or bar chart
Measures: AVG(fulfillment_days), COUNT(order_key)
Dimensions: dim_order_priority (priority_desc, priority_level)

-- 29. Backlog Analysis
Q29: "What is the current order backlog and how is it trending?"
Visual: Area chart
Measures: COUNT(CASE WHEN status_code IN ('O', 'P') THEN 1 END)
Dimensions: dim_date (order_date)

-- 30. Late Order Analysis
Q30: "What percentage of orders are fulfilled late by priority level?"
Visual: Stacked bar chart
Measures: COUNT(CASE WHEN fulfillment_days > target_days THEN 1 END) / COUNT(*)
Dimensions: dim_order_priority (priority_desc)
```

### Category 3: Customer Behavior & Segmentation

```powerbi
/*
DASHBOARD: Customer Analytics Dashboard
*/

-- 31. Customer Segmentation by Order Value
Q31: "How do different customer segments compare in terms of order value?"
Visual: Box plot or violin chart
Measures: AVG(total_amount), MEDIAN(total_amount)
Dimensions: dim_customer (market_segment)

-- 32. New vs Returning Customers
Q32: "What is the ratio of new vs returning customers over time?"
Visual: Stacked area chart
Measures: COUNT(DISTINCT customer_key) by cohort type
Dimensions: dim_date (order_date)

-- 33. High-Value Customer Identification
Q33: "Who are the top 100 customers by lifetime value?"
Visual: Table or bar chart with customer details
Measures: SUM(total_amount), COUNT(order_key), AVG(total_amount)
Dimensions: dim_customer (customer_name, market_segment)

-- 34. Customer Churn Risk
Q34: "Which customer segments show declining order frequency?"
Visual: Trend line with customer segments
Measures: AVG(days_between_orders), order_frequency_trend
Dimensions: dim_customer (market_segment, region_name)

-- 35. Geographic Customer Concentration
Q35: "Where are our most valuable customers located?"
Visual: Map visualization with bubble size
Measures: SUM(total_amount), COUNT(DISTINCT customer_key)
Dimensions: dim_customer (region_name, nation_name)
```

### Category 4: Temporal & Seasonal Patterns

```powerbi
/*
DASHBOARD: Temporal Analytics Dashboard
*/

-- 36. Peak Order Times
Q36: "What days of the week and months have the highest order volume?"
Visual: Calendar heatmap
Measures: COUNT(order_key)
Dimensions: dim_date (day_of_week, month, quarter)

-- 37. YoY Growth Analysis
Q37: "What is the year-over-year growth rate for orders and revenue?"
Visual: Line chart with growth indicators
Measures: SUM(total_amount) YoY %, COUNT(order_key) YoY %
Dimensions: dim_date (year, quarter)

-- 38. Weekday vs Weekend Order Analysis
Q38: "How do order patterns differ between weekdays and weekends?"
Visual: Side-by-side bar chart
Measures: COUNT(order_key), AVG(total_amount)
Dimensions: dim_date (is_weekend, day_of_week)

-- 39. Seasonal Product Preferences
Q39: "How do product category preferences change by season?"
Visual: Heatmap or stacked bar
Measures: SUM(quantity), SUM(total_amount)
Dimensions: dim_part (category), dim_date (quarter, month)

-- 40. Holiday Impact Analysis
Q40: "What is the impact of holidays on order volume and value?"
Visual: Line chart with holiday markers
Measures: COUNT(order_key), AVG(total_amount)
Dimensions: dim_date (full_date, is_holiday)
```

---

## FACT 3: fact_customer_lifetime (Customer Grain)
**🎯 Purpose:** Customer lifetime value, retention analytics, and loyalty programs

### Category 1: Customer Lifetime Value (CLV)

```powerbi
/*
DASHBOARD: CLV & Customer Value Dashboard
*/

-- 41. CLV Distribution
Q41: "What is the distribution of customer lifetime value across segments?"
Visual: Histogram or box plot
Measures: lifetime_value
Dimensions: dim_customer (market_segment, region_name)

-- 42. CLV by Acquisition Cohort
Q42: "How does CLV vary by customer acquisition cohort (first order year)?"
Visual: Cohort analysis chart
Measures: AVG(lifetime_value), MEDIAN(lifetime_value)
Dimensions: first_order_year, market_segment

-- 43. High-Value Customer Segmentation
Q43: "What characteristics define high-value vs low-value customers?"
Visual: Parallel coordinates or radar chart
Measures: lifetime_value, total_orders, avg_order_value, days_as_customer
Dimensions: dim_customer (market_segment, region_name)

-- 44. CLV Trend Over Time
Q44: "Is customer lifetime value increasing or decreasing over acquisition cohorts?"
Visual: Line chart with cohort analysis
Measures: AVG(lifetime_value) by acquisition month/year
Dimensions: first_order_date

-- 45. Profitability by Customer
Q45: "Which customers are most profitable (revenue minus estimated costs)?"
Visual: Pareto chart (80/20 analysis)
Measures: lifetime_value - estimated_costs
Dimensions: dim_customer (customer_name, market_segment)
```

### Category 2: Customer Retention & Churn

```powerbi
/*
DASHBOARD: Retention & Churn Dashboard
*/

-- 46. Customer Retention Rate
Q46: "What is the overall customer retention rate over time?"
Visual: Cohort retention table or line chart
Measures: retention_rate = customers_returning / customers_acquired
Dimensions: acquisition_cohort, months_since_acquisition

-- 47. Customer Lifetime Duration
Q47: "What is the average customer lifetime duration by segment?"
Visual: Bar chart with confidence intervals
Measures: AVG(days_as_customer), MEDIAN(days_as_customer)
Dimensions: dim_customer (market_segment)

-- 48. Churn Risk Factors
Q48: "What factors correlate with customer churn (low order frequency, low order value)?"
Visual: Decision tree or correlation matrix
Measures: churn_risk_score, avg_order_value, total_orders
Dimensions: market_segment, region_name

-- 49. Customer Activity Patterns
Q49: "How does customer activity change over their lifetime (order frequency trends)?"
Visual: Line chart showing activity over customer lifetime
Measures: AVG(orders_per_month) by months_since_first_order
Dimensions: market_segment

-- 50. Reactivation Success Rate
Q50: "What percentage of dormant customers return, and what brings them back?"
Visual: Funnel chart
Measures: COUNT(churned_customers), COUNT(reactivated_customers)
Dimensions: dim_customer (market_segment)
```

### Category 3: Customer Segmentation & Profiling

```powerbi
/*
DASHBOARD: Customer Segmentation Dashboard
*/

-- 51. RFM Analysis (Recency, Frequency, Monetary)
Q51: "How do customers cluster based on recency, frequency, and monetary value?"
Visual: RFM segmentation matrix (heatmap)
Measures: recency_days, total_orders, lifetime_value
Dimensions: dim_customer (all attributes)

-- 52. Customer Persona Development
Q52: "What are the distinct customer personas based on purchasing behavior?"
Visual: Clustering visualization (PCA or t-SNE)
Measures: avg_order_value, order_frequency, product_preferences, market_segment

-- 53. Geographic Customer Distribution
Q53: "How are customers distributed across regions and nations?"
Visual: Map with density heatmap
Measures: COUNT(customer_key), SUM(lifetime_value)
Dimensions: dim_customer (region_name, nation_name)

-- 54. Segment Migration Analysis
Q54: "How do customers migrate between segments over time?"
Visual: Sankey diagram
Measures: COUNT(customers) migrating from segment A to B
Dimensions: market_segment (current vs previous)

-- 55. Product Affinity by Segment
Q55: "What product categories are preferred by different customer segments?"
Visual: Heatmap or matrix
Measures: SUM(quantity), SUM(revenue)
Dimensions: dim_customer (market_segment), dim_part (category)
```

### Category 4: Customer Growth & Acquisition

```powerbi
/*
DASHBOARD: Customer Growth Dashboard
*/

-- 56. New Customer Acquisition Trends
Q56: "How many new customers are acquired over time, and what's the trend?"
Visual: Area chart with trend line
Measures: COUNT(DISTINCT customer_key WHERE first_order_date = date)
Dimensions: dim_date (first_order_date_key)

-- 57. Acquisition Cost Analysis
Q57: "What is the estimated acquisition cost per customer by segment?"
Visual: Bar chart
Measures: estimated_acquisition_cost, lifetime_value / acquisition_cost
Dimensions: dim_customer (market_segment, region_name)

-- 58. Customer Growth Rate
Q58: "What is the month-over-month customer growth rate?"
Visual: Line chart with growth indicators
Measures: new_customers, churned_customers, net_growth_rate
Dimensions: dim_date (month)

-- 59. Acquisition Channel Effectiveness
Q59: "Which acquisition channels produce the highest lifetime value customers?"
Visual: Bar chart with dual axes
Measures: COUNT(customers), AVG(lifetime_value)
Dimensions: acquisition_channel (from marketing data)

-- 60. Referral Value Analysis
Q60: "What is the network value of referred customers vs non-referred?"
Visual: Comparison chart
Measures: AVG(lifetime_value), total_orders, avg_order_value
Filter: is_referred = true vs false
```

---

## Cross-Fact Analytics (Combining Multiple Fact Tables)

```powerbi
/*
DASHBOARD: Enterprise-Wide Analytics
Combines insights from all three fact tables
*/

-- 61. Customer 360 View
Q61: "What is the complete view of a customer (orders, line items, lifetime value)?"
Visual: Drill-through page with customer details
Tables: fact_orders + fact_lineitem + fact_customer_lifetime
Measures: total_orders, lifetime_value, avg_order_value, product_preferences

-- 62. Product-Customer Profitability Matrix
Q62: "Which product-customer combinations are most profitable?"
Visual: Scatter plot matrix
Measures: profit_margin, order_frequency, lifetime_value
Dimensions: dim_part (product), dim_customer (segment)

-- 63. Operational vs Financial Metrics
Q63: "How do operational metrics (shipping time) correlate with financial metrics (revenue)?"
Visual: Scatter plot with trend line
Measures: AVG(delivery_days), SUM(revenue), return_rate
Dimensions: dim_date (time)

-- 64. Supplier-Customer Chain Analysis
Q64: "What is the end-to-end value chain from supplier to customer?"
Visual: Sankey diagram
Measures: revenue, quantity
Dimensions: dim_supplier → dim_part → dim_customer

-- 65. Predictive Analytics Dashboard
Q65: "What are the predicted next month's revenue, churn rate, and order volume?"
Visual: Forecast charts with confidence intervals
Models: Time series forecasting, churn prediction models
Measures: predicted_revenue, predicted_orders, predicted_churn_rate
```

---

## PowerBI Implementation Recommendations

### 1. **Data Model Structure**

```powerbi
/*
PowerBI Data Model Relationships
*/

-- Create a star schema in PowerBI
Relationships:
fact_lineitem (*) ←→ dim_date (1)  [ship_date_key]
fact_lineitem (*) ←→ dim_part (1)   [part_key]
fact_lineitem (*) ←→ dim_supplier (1) [supplier_key]

fact_orders (*) ←→ dim_date (1)     [order_date_key]
fact_orders (*) ←→ dim_customer (1) [customer_key]
fact_orders (*) ←→ dim_order_status (1)
fact_orders (*) ←→ dim_order_priority (1)

fact_customer_lifetime (1) ←→ dim_customer (1) [customer_key]

-- Connect dim_date to all facts for time intelligence
dim_date (1) ←→ fact_lineitem (*)
dim_date (1) ←→ fact_orders (*)
dim_date (1) ←→ fact_customer_lifetime (*)

-- Note: Do NOT connect fact tables directly to each other in PowerBI
-- Use DAX measures to combine insights when needed
```

### 2. **Recommended DAX Measures**

```dax
// Revenue Measures
Total Revenue = 
    SUMX(
        fact_lineitem,
        fact_lineitem[extended_price] * 
        (1 - fact_lineitem[discount]) * 
        (1 + fact_lineitem[tax])
    )

// YoY Growth
Revenue YoY % = 
    VAR CurrentYearRevenue = [Total Revenue]
    VAR PreviousYearRevenue = 
        CALCULATE(
            [Total Revenue],
            SAMEPERIODLASTYEAR(dim_date[full_date])
        )
    RETURN
        DIVIDE(CurrentYearRevenue - PreviousYearRevenue, PreviousYearRevenue)

// Customer Lifetime Value
Avg CLV by Segment = 
    AVERAGEX(
        VALUES(dim_customer[market_segment]),
        CALCULATE(AVERAGE(fact_customer_lifetime[lifetime_value]))
    )

// Order Fulfillment Rate
OnTime Delivery % = 
    DIVIDE(
        COUNTROWS(
            FILTER(
                fact_orders,
                fact_orders[fulfillment_days] <= 
                RELATED(dim_order_priority[target_days])
            )
        ),
        COUNTROWS(fact_orders)
    )

// Customer Retention Rate
Retention Rate = 
    VAR CurrentPeriodCustomers = 
        VALUES(fact_orders[customer_key])
    VAR PreviousPeriodCustomers = 
        CALCULATETABLE(
            VALUES(fact_orders[customer_key]),
            PREVIOUSPERIOD(dim_date[full_date])
        )
    RETURN
        DIVIDE(
            COUNTROWS(INTERSECT(CurrentPeriodCustomers, PreviousPeriodCustomers)),
            COUNTROWS(PreviousPeriodCustomers)
        )
```

### 3. **Dashboard Layout by Role**

```powerbi
/*
Role-Based Dashboard Strategy
*/

-- Executive Dashboard (Monthly Review)
Pages:
1. Company Overview: Revenue, Orders, Customers (KPIs)
2. Growth Trends: YoY comparisons, forecasts
3. Customer Health: CLV trends, retention rates
4. Operational Excellence: Fulfillment rates, shipping metrics

-- Sales Team Dashboard (Daily/Weekly)
Pages:
1. Sales Performance: Revenue by region, product, segment
2. Top Customers: High-value customers, opportunities
3. Product Performance: Best/worst selling products
4. Discount Analysis: Discount effectiveness, margin impact

-- Operations Dashboard (Daily)
Pages:
1. Order Fulfillment: Backlog, on-time delivery
2. Shipping Metrics: Carrier performance, delays
3. Return Analysis: Return rates by product, region
4. Supplier Performance: Quality, delivery times

-- Marketing Dashboard (Weekly/Monthly)
Pages:
1. Customer Acquisition: New customers, acquisition costs
2. Segmentation: RFM analysis, persona breakdown
3. Retention: Churn analysis, reactivation campaigns
4. Campaign ROI: Campaign performance, lift analysis
```

### 4. **Key Performance Indicators (KPIs)**

```powerbi
/*
Strategic KPIs for Executive Dashboard
*/

Financial KPIs:
- Total Revenue (TTM)
- Revenue Growth (YoY, QoQ)
- Average Order Value (AOV)
- Gross Margin %
- Customer Lifetime Value (CLV)

Operational KPIs:
- Order Fulfillment Rate
- Average Delivery Time
- Return Rate %
- Supplier Quality Score
- Inventory Turnover

Customer KPIs:
- Customer Acquisition Cost (CAC)
- Retention Rate
- Churn Rate
- Net Promoter Score (NPS)
- Customer Satisfaction Score

Product KPIs:
- Top 10 Products by Revenue
- Product Category Growth
- Discount Effectiveness
- New Product Adoption Rate
```


















# FACT 4: fact_partsupp (Part-Supplier Grain) (NEEDS SUPER REVISION)

## Understanding the Part-Supplier Relationship

Before diving into the questions, let me explain what `fact_partsupp` represents and why it's crucial for supply chain analytics.


## Business Questions for fact_partsupp

### Category 1: Supply Chain Cost Analysis

```powerbi
/*
DASHBOARD: Cost Optimization Dashboard
Focus: Understanding supply costs and identifying savings opportunities
*/

-- 1. Supplier Cost Comparison by Part
Q1: "For each part, which suppliers offer the lowest supply cost?"
Visual: Bar chart with part breakdown
Measures: MIN(supply_cost), AVG(supply_cost)
Dimensions: dim_part (part_name, type), dim_supplier (supplier_name)
Insight: Identify cost leaders per product category

-- 2. Total Inventory Value by Part Category
Q2: "What is the total inventory value (available quantity × supply cost) by product category?"
Visual: Treemap or sunburst chart
Measures: SUM(available_quantity * supply_cost) as total_value
Dimensions: dim_part (category, type, brand)
Insight: Where is most capital tied up in inventory?

-- 3. Supply Cost Variance Analysis
Q3: "What is the price variance for the same part across different suppliers?"
Visual: Box plot or violin chart
Measures: MIN(supply_cost), MAX(supply_cost), AVG(supply_cost), STDDEV(supply_cost)
Dimensions: dim_part (part_name, type)
Insight: Identify parts with high price volatility

-- 4. Supplier Cost Position by Region
Q4: "How do supply costs compare across supplier regions?"
Visual: Map with color-coded markers
Measures: AVG(supply_cost), COUNT(supplier_key)
Dimensions: dim_geography (region_name, nation_name)
Insight: Geographic cost advantages/disadvantages

-- 5. Economies of Scale Analysis
Q5: "Is there a correlation between available quantity and supply cost per unit?"
Visual: Scatter plot with trend line
Measures: available_quantity, supply_cost
Dimensions: dim_part (type), dim_supplier (region)
Insight: Identify optimal order quantities for cost efficiency
```

### Category 2: Supplier Performance & Quality

```powerbi
/*
DASHBOARD: Supplier Performance Dashboard
Focus: Evaluating and optimizing supplier relationships
*/

-- 6. Supplier Quality Rating Dashboard
Q6: "Which suppliers have the highest quality ratings across their parts portfolio?"
Visual: Performance scorecard (Top 20 suppliers)
Measures: AVG(quality_rating), COUNT(DISTINCT part_key)
Dimensions: dim_supplier (supplier_name, region_name)
Insight: Identify quality leaders and laggards

-- 7. Supplier Reliability Score
Q7: "Which suppliers consistently maintain adequate stock levels?"
Visual: Heatmap of availability by supplier
Measures: AVG(available_quantity), MIN(available_quantity) trends
Dimensions: dim_supplier (supplier_name), dim_part (type)
Insight: Identify suppliers with stockout risks

-- 8. Preferred Supplier Analysis
Q8: "What characteristics define preferred vs non-preferred suppliers?"
Visual: Parallel coordinates or radar chart
Measures: AVG(supply_cost), AVG(quality_rating), AVG(lead_time_days), is_preferred
Dimensions: dim_supplier (region, size category)
Insight: Understand what makes a supplier "preferred"

-- 9. Supplier Concentration Risk
Q9: "Which parts have a single supplier (high risk) vs multiple suppliers?"
Visual: Pie chart + detail table
Measures: COUNT(DISTINCT supplier_key) per part
Dimensions: dim_part (part_name, type)
Insight: Identify single-source dependencies and risk exposure

-- 10. Supplier Performance Trends
Q10: "How is supplier quality and cost trending over time?"
Visual: Line chart with supplier segmentation
Measures: AVG(quality_rating), AVG(supply_cost) over time
Dimensions: dim_supplier (supplier_name), last_updated (monthly)
Insight: Track supplier improvement or deterioration
```

### Category 3: Inventory & Stock Management

```powerbi
/*
DASHBOARD: Inventory Optimization Dashboard
Focus: Maintaining optimal stock levels and reducing carrying costs
*/

-- 11. Inventory Value Distribution
Q11: "How is total inventory value distributed across product categories?"
Visual: Waterfall chart or stacked bar
Measures: SUM(available_quantity * supply_cost)
Dimensions: dim_part (category, type, brand)
Insight: Identify where inventory capital is concentrated

-- 12. Stock Level Alert System
Q12: "Which part-supplier combinations are below minimum stock threshold?"
Visual: Red/Yellow/Green traffic light dashboard
Measures: available_quantity, safety_stock_level
Dimensions: dim_part (part_name), dim_supplier (supplier_name)
Insight: Proactive shortage alerts and reorder recommendations

-- 13. Excess Inventory Analysis
Q13: "Which parts have excessive stock levels (>90 days supply) by category?"
Visual: Pareto chart (80/20 rule)
Measures: days_of_supply = available_quantity / avg_daily_demand
Dimensions: dim_part (type, category)
Insight: Identify slow-moving inventory for reduction

-- 14. Inventory Turnover by Category
Q14: "What is the inventory turnover rate by product category?"
Visual: Bar chart with benchmarks
Measures: turnover_rate = COGS / average_inventory_value
Dimensions: dim_part (category, type)
Insight: Identify fast vs slow-moving products

-- 15. Seasonal Stock Requirements
Q15: "How do optimal stock levels vary by season for different part types?"
Visual: Heatmap (month × part type)
Measures: optimal_stock_level, current_stock_level
Dimensions: dim_part (type), seasonality patterns
Insight: Seasonal inventory planning
```

### Category 4: Procurement & Contract Strategy

```powerbi
/*
DASHBOARD: Procurement Strategy Dashboard
Focus: Optimizing purchasing decisions and contract negotiations
*/

-- 16. Contract Coverage Analysis
Q16: "What percentage of our supply is under contract vs spot purchases?"
Visual: Donut chart with trend over time
Measures: COUNT(parts) under contract, AVG(supply_cost)
Dimensions: dim_contract_terms (contract_type)
Insight: Contract strategy effectiveness

-- 17. Lead Time Impact Analysis
Q17: "How does supplier lead time correlate with cost and quality?"
Visual: Scatter plot matrix (lead_time × cost × quality)
Measures: AVG(lead_time_days), AVG(supply_cost), AVG(quality_rating)
Dimensions: dim_supplier (region, size)
Insight: Trade-offs between speed, cost, and quality

-- 18. Supplier Negotiation Leverage
Q18: "Which suppliers have the most negotiation leverage (critical parts, high volume)?"
Visual: Bubble chart (volume vs criticality vs cost)
Measures: COUNT(parts), SUM(available_quantity), AVG(supply_cost)
Dimensions: dim_supplier (supplier_name)
Insight: Identify strategic supplier relationships

-- 19. Total Cost of Ownership (TCO) Analysis
Q19: "What is the true total cost of ownership for each supplier (price + lead time + quality)?"
Visual: Multi-metric scorecard
Measures: weighted_tco = supply_cost + (lead_time_days * inventory_carry_cost) + (quality_rating * quality_penalty)
Dimensions: dim_supplier (supplier_name)
Insight: Beyond purchase price to true cost

-- 20. Supplier Consolidation Opportunities
Q20: "Which part categories could benefit from supplier consolidation?"
Visual: Matrix (part category × number of suppliers)
Measures: COUNT(DISTINCT supplier_key), AVG(supply_cost), AVG(quality_rating)
Dimensions: dim_part (category)
Insight: Identify consolidation savings opportunities
```

### Category 5: Strategic Sourcing & Risk Management

```powerbi
/*
DASHBOARD: Strategic Sourcing Dashboard
Focus: Long-term supply chain strategy and risk mitigation
*/

-- 21. Geographic Supply Chain Risk
Q21: "What is our geographic supply concentration and associated risks?"
Visual: Map with risk heat overlay
Measures: COUNT(suppliers), SUM(inventory_value), geopolitical_risk_score
Dimensions: dim_geography (region, nation)
Insight: Identify geographic concentration risks

-- 22. Supplier Diversification Index
Q22: "Which parts have healthy supplier diversification vs dangerous concentration?"
Visual: Gauge chart with diversification score
Measures: supplier_diversity_index = 1 - (top_supplier_share / total_share)
Dimensions: dim_part (category, type)
Insight: Measure and improve supply chain resilience

-- 23. Critical Part Identification
Q23: "Which parts are most critical to our business (high value, single source, long lead time)?"
Visual: Risk matrix (impact vs likelihood)
Measures: criticality_score = (value_weight * 0.4) + (single_source * 0.3) + (lead_time * 0.3)
Dimensions: dim_part (part_name, type)
Insight: Focus risk mitigation on critical items

-- 24. Supplier Financial Health Assessment
Q24: "What is the financial health profile of our key suppliers?"
Visual: Financial scorecard with trend arrows
Measures: financial_risk_score, payment_terms_compliance, on_time_delivery
Dimensions: dim_supplier (supplier_name)
Insight: Identify suppliers at risk of bankruptcy

-- 25. Sustainability & Compliance Metrics
Q25: "How do our suppliers perform on sustainability and compliance metrics?"
Visual: Radar chart (multiple dimensions)
Measures: sustainability_score, compliance_score, carbon_footprint, ethical_rating
Dimensions: dim_supplier (region, size)
Insight: ESG (Environmental, Social, Governance) tracking
```

### Category 6: Cost Optimization & Savings

```powerbi
/*
DASHBOARD: Cost Savings Dashboard
Focus: Identifying and tracking cost reduction opportunities
*/

-- 26. Cost Savings Opportunities
Q26: "What are the top 20 cost-saving opportunities by switching suppliers?"
Visual: Bar chart with savings potential
Measures: potential_savings = (current_cost - best_alternative_cost) * annual_volume
Dimensions: dim_part (part_name), dim_supplier
Insight: Actionable cost reduction targets

-- 27. Price Trend Analysis
Q27: "How are supply costs trending for key raw materials?"
Visual: Line chart with commodity indices
Measures: AVG(supply_cost) over time, market_price_index
Dimensions: dim_part (category, material_type)
Insight: Track inflation and deflation trends

-- 28. Volume Discount Analysis
Q28: "Do we receive volume discounts from suppliers (cost decreases with quantity)?"
Visual: Scatter plot (quantity vs cost per unit)
Measures: available_quantity, supply_cost
Dimensions: dim_supplier (supplier_name), dim_part (type)
Insight: Validate volume discount effectiveness

-- 29. Transportation Cost Impact
Q29: "How does supplier distance affect total landed cost?"
Visual: Scatter plot (distance vs total_cost)
Measures: supplier_distance, supply_cost, estimated_transport_cost
Dimensions: dim_geography, dim_part (weight, volume)
Insight: Optimize supplier location selection

-- 30. Year-over-Year Savings Tracking
Q30: "What are our year-over-year supply cost savings by category?"
Visual: Waterfall chart showing changes
Measures: current_cost vs previous_year_cost, savings_percentage
Dimensions: dim_part (category), last_updated
Insight: Track procurement performance over time
```

### Category 7: Production & Demand Planning

```powerbi
/*
DASHBOARD: Production Planning Dashboard
Focus: Aligning supply with production demand
*/

-- 31. Supply vs Demand Gap Analysis
Q31: "Which part-supplier combinations have supply gaps relative to forecasted demand?"
Visual: Gap analysis chart (supply vs demand)
Measures: available_quantity, forecasted_demand, gap = demand - supply
Dimensions: dim_part (part_name), dim_supplier
Insight: Identify shortages before they impact production

-- 32. Safety Stock Optimization
Q32: "What are the optimal safety stock levels for each part category?"
Visual: Optimization curve (service level vs inventory cost)
Measures: current_safety_stock, recommended_safety_stock, service_level
Dimensions: dim_part (category, lead_time_category)
Insight: Balance service levels with inventory costs

-- 33. Lead Time Reliability
Q33: "Which suppliers consistently meet their stated lead times?"
Visual: Reliability scorecard
Measures: actual_lead_time, promised_lead_time, reliability_score
Dimensions: dim_supplier (supplier_name), dim_part (type)
Insight: Identify reliable vs unreliable suppliers

-- 34. Capacity Planning
Q34: "What is the maximum supply capacity by part category?"
Visual: Bar chart with capacity utilization
Measures: current_supply, max_capacity, utilization_percentage
Dimensions: dim_part (category), dim_supplier (region)
Insight: Identify capacity constraints

-- 35. New Product Introduction (NPI) Readiness
Q35: "Are we supply-ready for new product launches?"
Visual: Readiness dashboard
Measures: supplier_qualified, tooling_complete, sample_approved, production_ready
Dimensions: dim_part (new_products), dim_supplier
Insight: NPI risk assessment
```

---

## Advanced Analytics & Cross-Fact Integration

```powerbi
/*
DASHBOARD: Integrated Supply Chain Analytics
Combines fact_partsupp with other fact tables
*/

-- 36. End-to-End Cost Analysis
Q36: "What is the complete cost structure from supplier purchase to customer sale?"
Visual: Sankey diagram (cost flow)
Tables: fact_partsupp + fact_lineitem
Measures: supply_cost + manufacturing_cost + shipping_cost + margin
Insight: Full product profitability

-- 37. Supplier Contribution to Revenue
Q37: "Which suppliers contribute most to our revenue (through their parts)?"
Visual: Treemap (supplier → parts → revenue)
Tables: fact_partsupp + fact_lineitem
Measures: total_revenue from parts, profit_margin
Dimensions: dim_supplier, dim_part
Insight: Strategic supplier importance

-- 38. Quality Impact on Returns
Q38: "How does supplier quality rating correlate with customer return rates?"
Visual: Scatter plot with trend line
Tables: fact_partsupp + fact_lineitem (return_flag)
Measures: quality_rating, return_rate
Dimensions: dim_supplier
Insight: Quality's financial impact

-- 39. Supply Chain Agility Score
Q39: "How quickly can we respond to demand changes across product categories?"
Visual: Spider chart
Measures: lead_time, supplier_flexibility, inventory_levels, production_capacity
Dimensions: dim_part (category)
Insight: Supply chain responsiveness

-- 40. Total Supply Chain Cost Dashboard
Q40: "What is the total supply chain cost by region and product category?"
Visual: Matrix with drill-down
Tables: fact_partsupp + fact_lineitem + dim_geography
Measures: SUM(supply_cost) + SUM(shipping_cost) + SUM(inventory_carry_cost)
Dimensions: region, product_category, time
Insight: Cost transparency and benchmarking
```

---

## PowerBI Implementation Strategy for fact_partsupp

### 1. **Data Model Relationships**

```powerbi
/*
PowerBI Model for fact_partsupp
*/

Relationships:
fact_partsupp (*) ←→ dim_part (1) [part_key]
fact_partsupp (*) ←→ dim_supplier (1) [supplier_key]
fact_partsupp (*) ←→ dim_geography (1) [via supplier region]
fact_partsupp (*) ←→ dim_quality_metrics (1) [quality_rating]
fact_partsupp (*) ←→ dim_contract_terms (1) [contract_type]

-- Connect to other facts for integrated analysis
dim_part (1) ←→ fact_lineitem (*)  [for revenue analysis]
dim_supplier (1) ←→ fact_lineitem (*) [for supplier revenue contribution]
```

### 2. **Key DAX Measures for fact_partsupp**

```dax
// Inventory Metrics
Total Inventory Value = 
    SUMX(
        fact_partsupp,
        fact_partsupp[available_quantity] * fact_partsupp[supply_cost]
    )

// Supplier Concentration Risk
Supplier Concentration Score = 
    VAR TopSupplierShare = 
        DIVIDE(
            CALCULATE([Total Inventory Value], TOPN(1, dim_supplier, [Total Inventory Value])),
            [Total Inventory Value]
        )
    RETURN
        IF(TopSupplierShare > 0.5, "High Risk", 
           IF(TopSupplierShare > 0.3, "Medium Risk", "Low Risk"))

// Quality Score (Weighted)
Weighted Quality Score = 
    DIVIDE(
        SUMX(
            fact_partsupp,
            fact_partsupp[quality_rating] * fact_partsupp[available_quantity]
        ),
        SUM(fact_partsupp[available_quantity])
    )

// Lead Time Performance
Lead Time Reliability = 
    DIVIDE(
        COUNTROWS(FILTER(fact_partsupp, fact_partsupp[actual_lead_time] <= fact_partsupp[promised_lead_time])),
        COUNTROWS(fact_partsupp)
    )

// Total Cost of Ownership (TCO)
TCO per Unit = 
    fact_partsupp[supply_cost] + 
    (fact_partsupp[lead_time_days] * [Daily Inventory Cost]) +
    ((1 - fact_partsupp[quality_rating]) * [Quality Penalty Cost])

// Strategic Sourcing KPIs
Strategic Supplier Score = 
    SWITCH(
        TRUE(),
        [Quality Score] > 0.9 && [Lead Time Reliability] > 0.95 && [Total Cost] < [Market Average], "Strategic Partner",
        [Quality Score] > 0.8 && [Lead Time Reliability] > 0.9, "Preferred Supplier",
        [Quality Score] > 0.7, "Approved Supplier",
        "Under Review"
    )
```

### 3. **Role-Based Dashboards**

```powerbi
/*
Role-Specific Dashboards for fact_partsupp
*/

-- Procurement Team Dashboard (Daily)
Pages:
1. Supplier Performance Scorecard
2. Cost Savings Tracker
3. Contract Compliance Monitor
4. Negotiation Opportunities

-- Supply Chain Planning Dashboard (Weekly)
Pages:
1. Inventory Health Monitor
2. Lead Time Performance
3. Supply vs Demand Gap
4. Safety Stock Optimization

-- Executive Dashboard (Monthly)
Pages:
1. Supply Chain Cost Trends
2. Supplier Risk Heatmap
3. Strategic Sourcing ROI
4. Supply Chain Agility Score

-- Quality Management Dashboard (Daily)
Pages:
1. Supplier Quality Ratings
2. Defect Rate Trends
3. Corrective Action Tracking
4. Quality Improvement Initiatives
```

### 4. **Strategic KPIs for fact_partsupp**

```powerbi
/*
Strategic KPIs for Executive Dashboard
*/

Supply Chain KPIs:
- Total Inventory Value (with trend)
- Inventory Turnover Ratio
- Days of Inventory Outstanding (DIO)
- Supplier Quality Score (weighted)
- On-Time Delivery Rate

Cost KPIs:
- Total Supply Cost (with YoY change)
- Cost Savings Achieved
- Cost Avoidance
- Total Cost of Ownership (TCO)
- Purchase Price Variance (PPV)

Risk KPIs:
- Supplier Concentration Risk Score
- Single-Source Part Percentage
- Geographic Risk Exposure
- Supplier Financial Health Score
- Lead Time Volatility Index

Operational KPIs:
- Supplier Lead Time Reliability
- Stockout Frequency
- Order Fill Rate
- Supplier Capacity Utilization
- New Supplier Qualification Rate

Strategic KPIs:
- Strategic Supplier Spend Percentage
- Supplier Innovation Index
- Sustainability Compliance Rate
- Supplier Development ROI
- Supply Chain Agility Score
```

---

**fact_partsupp** is the **bridge between procurement and sales**, enabling end-to-end supply chain optimization. It answers critical questions about supplier performance, inventory health, cost optimization, and strategic sourcing that directly impact profitability and operational efficiency.
