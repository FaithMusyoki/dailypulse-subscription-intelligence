# DAILYPULSE MEDIA

## Subscription Intelligence — Business Requirements Document

**Project:** DAILYPULSE Subscription Intelligence

**Version:** 1.0

**Industry:** Digital Media & Publishing

**Project Type:** End-to-End Data Analytics & Data Science Portfolio Project

---

## 1. Business Overview

DAILYPULSE MEDIA is a fictional digital-first media company offering paid access to digital news, premium journalism, electronic newspapers and corporate media subscriptions.

The business operates several subscription products across different billing frequencies, including daily, weekly, monthly and annual plans.

As the subscriber base grows, management requires a more comprehensive understanding of customer behaviour, subscription performance and revenue.

The purpose of the Subscription Intelligence project is to develop an analytics environment capable of supporting data-driven decisions across revenue growth, customer acquisition, retention, subscription migration and churn.

---

## 2. Business Problem

DAILYPULSE MEDIA currently has limited visibility into the complete subscriber lifecycle.

Although management can track basic measures such as subscriber counts and revenue, several important questions remain difficult to answer.

These include:

* Which products and billing cycles generate the most revenue?
* Which subscribers are most likely to renew or churn?
* How do customers migrate between subscription plans?
* Which acquisition channels attract the most valuable customers?
* Are customers acquired through promotions retained over time?
* Which subscription products have the highest retention rates?
* How much revenue is lost through churn?
* Which customers are most likely to upgrade or downgrade?
* How does subscriber behaviour affect long-term customer value?

The business therefore requires a central subscription intelligence capability that can move beyond basic reporting toward deeper customer and revenue analysis.

---

## 3. Business Objectives

The project aims to help DAILYPULSE MEDIA:

1. Monitor subscription and revenue performance.
2. Increase paid subscriber growth.
3. Improve free-trial-to-paid conversion.
4. Improve subscriber retention.
5. Reduce voluntary and involuntary churn.
6. Increase migration toward higher-value subscription plans.
7. Identify high-value and at-risk customer segments.
8. Measure customer lifetime value.
9. Evaluate acquisition-channel performance.
10. Improve revenue forecasting.
11. Provide management with clear and actionable subscription insights.

---

## 4. Subscription Product Catalogue

DAILYPULSE MEDIA offers six core subscription products.

| Product          | Daily | Weekly | Monthly | Annual |
| ---------------- | :---: | :----: | :-----: | :----: |
| Digital Basic    |   ✓   |    ✓   |    ✓    |    ✓   |
| Digital Premium  |   —   |    ✓   |    ✓    |    ✓   |
| Daily ePaper     |   ✓   |    ✓   |    ✓    |    ✓   |
| Weekend ePaper   |   —   |    ✓   |    ✓    |    —   |
| Student Digital  |   —   |    ✓   |    ✓    |    ✓   |
| Corporate ePaper |   —   |    —   |    ✓    |    ✓   |

The business also offers a **7-day free trial** to eligible individual customers.

The free trial represents an acquisition stage rather than a paid subscription product.

---

## 5. Working Subscription Rate Card

The following prices are fictional assumptions created specifically for this portfolio project and may be refined as the project develops.

| Product          |  Daily |  Weekly |   Monthly |     Annual |
| ---------------- | -----: | ------: | --------: | ---------: |
| Digital Basic    | KES 30 | KES 150 |   KES 500 |  KES 5,000 |
| Digital Premium  |      — | KES 250 |   KES 800 |  KES 8,000 |
| Daily ePaper     | KES 60 | KES 300 | KES 1,000 | KES 10,000 |
| Weekend ePaper   |      — | KES 150 |   KES 500 |          — |
| Student Digital  |      — | KES 100 |   KES 300 |  KES 3,000 |
| Corporate ePaper |      — |       — |  Variable |   Variable |

Annual subscriptions are priced to provide an effective discount compared with continuously renewing shorter-term subscriptions.

This allows the business to evaluate whether longer-term discounts result in higher retention and customer lifetime value.

---

## 6. Corporate Subscription Model

Corporate subscriptions are purchased by organisations rather than individual customers.

DAILYPULSE MEDIA offers both:

* Monthly corporate subscriptions
* Annual corporate subscriptions

Corporate accounts may purchase access for multiple employees.

### Corporate Seats

A **seat** represents one licensed user under a corporate subscription.

For example, an organisation purchasing 50 seats may provide individual access to up to 50 employees while receiving one centrally managed corporate subscription.

Corporate subscription analysis should therefore distinguish between:

* Corporate account
* Number of seats purchased
* Number of seats activated
* Monthly or annual contract
* Total contract value
* Revenue per seat
* Account renewal
* Seat expansion
* Seat reduction
* Corporate churn

Corporate pricing will be determined according to the number of seats purchased and the billing term.

---

## 7. Customer Lifecycle

DAILYPULSE MEDIA customers may move through several stages during their relationship with the business.

A typical individual customer journey may follow:

```text
Visitor
   ↓
Registered User
   ↓
Free Trial
   ↓
Paid Subscriber
   ↓
Renewal
   ↓
Upgrade / Downgrade
   ↓
Continued Subscription
   ↓
Churn
   ↓
Possible Reactivation
```

However, customers may follow different paths.

Examples include:

```text
Free Trial → Daily → Weekly → Monthly → Annual
```

```text
Free Trial → Daily → Churn
```

```text
Annual → Monthly → Weekly → Churn
```

```text
Monthly → Churn → Reactivation → Annual
```

The analytics environment must preserve these historical movements rather than only recording a customer's current subscription.

---

## 8. Subscription Events

Customer lifecycle activity will be captured as individual subscription events.

Events may include:

| Event                   | Description                                 |
| ----------------------- | ------------------------------------------- |
| `trial_started`         | Customer begins a free trial                |
| `trial_converted`       | Free trial converts to a paid subscription  |
| `subscription_started`  | Customer starts a paid subscription         |
| `renewed`               | Existing subscription successfully renews   |
| `upgraded`              | Customer moves to a higher-value plan       |
| `downgraded`            | Customer moves to a lower-value plan        |
| `billing_cycle_changed` | Customer changes billing frequency          |
| `payment_successful`    | Payment is completed                        |
| `payment_failed`        | Payment attempt fails                       |
| `grace_period_started`  | Customer enters a temporary grace period    |
| `cancelled`             | Customer requests cancellation              |
| `expired`               | Subscription reaches its expiry date        |
| `churned`               | Customer becomes inactive                   |
| `reactivated`           | Former subscriber starts a new subscription |

Capturing subscription events will make it possible to reconstruct complete customer journeys over time.

---

## 9. Churn Definitions

For this project, churn will be divided into three categories.

### Voluntary Churn

A subscriber deliberately chooses to cancel their subscription.

### Involuntary Churn

A subscription terminates because of circumstances such as:

* Failed payment
* Expired payment method
* Repeated unsuccessful renewal attempts

### Expiry Churn

A fixed-term subscriber reaches the end of their subscription period and does not renew within the defined renewal or grace period.

Corporate churn occurs when an organisation ends or fails to renew its corporate subscription.

---

## 10. Customer Acquisition Channels

Each newly acquired customer should have an identifiable acquisition source.

Potential channels include:

* Organic Search
* Direct
* Email
* Social Media
* Paid Search
* Paid Social
* Referral
* Affiliate / Partner
* Corporate Sales
* Campus Activation
* Promotional Campaign

This will allow customer acquisition to be evaluated beyond initial conversion.

The project should ultimately compare acquisition channels based on measures such as:

* Subscribers acquired
* Conversion rate
* Customer acquisition cost
* Retention
* Revenue
* Customer lifetime value

---

## 11. Core KPI Framework

### Subscriber Growth

* New Subscribers
* Active Subscribers
* Paid Subscribers
* Subscriber Growth Rate
* Trial Registrations
* Trial-to-Paid Conversion Rate
* Reactivated Subscribers

### Revenue

* Gross Subscription Revenue
* Net Subscription Revenue
* Revenue Growth
* Revenue by Product
* Revenue by Billing Frequency
* Monthly Recurring Revenue
* Annual Recurring Revenue
* Average Revenue Per User
* Average Revenue Per Paying User

### Retention

* Renewal Rate
* Retention Rate
* Churn Rate
* Voluntary Churn Rate
* Involuntary Churn Rate
* Cohort Retention
* Average Customer Tenure

### Customer Value

* Customer Lifetime Value
* Revenue per Customer
* Average Subscription Duration
* Upgrade Rate
* Downgrade Rate
* Reactivation Rate

### Marketing Performance

* Customer Acquisition Cost
* Conversion Rate
* Cost per Acquisition
* Trial Conversion Rate
* Revenue by Acquisition Channel
* Customer Lifetime Value by Acquisition Channel
* LTV-to-CAC Ratio

### Corporate Performance

* Active Corporate Accounts
* Corporate Revenue
* Average Contract Value
* Seats Purchased
* Seats Activated
* Seat Utilisation
* Revenue per Seat
* Corporate Renewal Rate
* Corporate Churn Rate

---

## 12. Subscription Migration Analysis

The project should measure how customers move between subscription products and billing frequencies.

Examples include:

```text
Daily → Weekly
Weekly → Monthly
Monthly → Annual
```

and:

```text
Digital Basic → Digital Premium
```

Key migration metrics will include:

* Upgrade Rate
* Downgrade Rate
* Billing-Cycle Migration
* Product Migration
* Post-Migration Retention
* Revenue Impact of Upgrades
* Revenue Impact of Downgrades

Migration analysis should help determine whether certain customer journeys are associated with stronger retention and greater customer lifetime value.

---

## 13. Key Business Questions

### Executive Management

* Are subscriptions growing?
* Is subscription revenue growing?
* Which products are driving growth?
* Which products are underperforming?
* Is subscriber growth translating into sustainable revenue?
* What are the major risks to future subscription performance?

### Product Team

* Which subscription products have the highest retention?
* Which billing cycles experience the highest churn?
* How do subscribers migrate between plans?
* Which products generate the most upgrades?
* Does upgrading improve subsequent retention?

### Marketing Team

* Which acquisition channels generate the most subscribers?
* Which channels generate the highest-value customers?
* Which campaigns produce the strongest retention?
* Are promotional offers attracting loyal customers or primarily discount-sensitive customers?
* Which acquisition channels generate the highest customer lifetime value?

### Customer Retention Team

* Which subscribers are most likely to churn?
* When does churn most commonly occur?
* Which behavioural patterns appear before churn?
* Which subscriber groups should receive retention interventions?
* What factors are associated with successful reactivation?

### Finance Team

* How much subscription revenue is being generated?
* How much revenue is being lost through churn?
* How much revenue comes from each product and billing cycle?
* What revenue should the business expect next month or quarter?
* What is the financial impact of improving retention?

### Corporate Sales

* Which corporate accounts generate the most revenue?
* What is the average corporate contract value?
* How effectively are purchased seats being utilised?
* Which accounts are expanding or reducing seats?
* Are monthly or annual corporate customers more likely to renew?

---

## 14. Reporting Requirements

The analytics environment should ultimately support three primary reporting views.

### Executive Subscription Dashboard

Designed for senior management and focused on:

* Subscribers
* Revenue
* Growth
* Churn
* Retention
* ARPU
* Performance trends
* Revenue forecast

### Subscription Performance Dashboard

Designed for product and commercial teams and focused on:

* Products
* Billing cycles
* Renewals
* Cohorts
* Upgrades
* Downgrades
* Plan migrations
* Churn

### Customer Intelligence Dashboard

Designed to provide deeper customer-level insights including:

* Customer segments
* Acquisition sources
* Retention patterns
* Customer lifetime value
* Churn risk
* Reactivation
* Customer behaviour

---

## 15. Analytical Maturity

The project should progressively move through four levels of analytics.

### Descriptive Analytics

**What happened?**

Examples:

* Revenue generated
* Subscriber growth
* Number of renewals
* Number of cancellations

### Diagnostic Analytics

**Why did it happen?**

Examples:

* Which products caused revenue growth?
* Which subscriber groups drove churn?
* Which channels generated the highest retention?

### Predictive Analytics

**What is likely to happen next?**

Examples:

* Which subscribers are most likely to churn?
* What will subscription revenue look like next quarter?
* Which subscribers are likely to upgrade?

### Prescriptive Analytics

**What should the business do?**

Examples:

* Which subscribers should receive retention offers?
* Which billing cycle should marketing promote?
* Which acquisition channels deserve greater investment?
* Which customer segments should be targeted for upgrades?

---

## 16. Data Requirements

The analytics environment will require data covering several business areas.

These are expected to include:

* Customers
* Products
* Subscription plans
* Subscriptions
* Subscription events
* Payments
* Marketing touchpoints
* Customer engagement
* Corporate accounts
* Corporate users
* Support interactions

The detailed database structure and relationships between these entities will be documented separately in the project's Entity Relationship Diagram and Data Dictionary.

---

## 17. Project Success Criteria

The project will be considered successful when the resulting analytics environment can reliably answer:

1. What happened?
2. Why did it happen?
3. Which customers, products or channels contributed to it?
4. What is likely to happen next?
5. What should the business do in response?

The final output should therefore go beyond reporting numbers and provide actionable recommendations.

For example, rather than reporting:

> Churn increased during the month.

The analysis should aim to identify:

> Churn is disproportionately concentrated among short-term Digital Basic subscribers acquired through promotional campaigns during their early subscription lifecycle, indicating a potential opportunity to improve onboarding and encourage migration toward longer-term plans.

---

## 18. Project Scope

This BRD establishes the business requirements for the DAILYPULSE Subscription Intelligence project.

The next stages of the project will include:

1. Entity Relationship Diagram
2. Data Dictionary
3. Synthetic Data Generation
4. PostgreSQL Database Development
5. SQL Analysis
6. Exploratory Data Analysis
7. Business Intelligence Dashboards
8. Customer Lifecycle Analysis
9. Churn Analysis and Prediction
10. Customer Segmentation
11. Revenue Forecasting
12. Additional Data Science Applications

All datasets, analytics and models developed during the project should trace back to the business requirements defined in this document.

---

## 19. Project Disclaimer

DAILYPULSE MEDIA is a fictional company created for portfolio and educational purposes.

The datasets, customers, transactions, subscription activity and financial values used in this project will be synthetically generated and will not represent real customer information.

The project is designed to simulate a realistic subscription-based media business environment for the purpose of demonstrating practical data analytics and data science skills.
