# billing-platform

Invoice Generation Strategy

- invoices are auto-generated every day
- generation only considers subscriptions whose NextBillingDate <= now
- after billing a subscription base item, its NextBillingDate is advanced by the billing interval
- overage is tied to the same customer, the same subscription, and the previous billing period
- real usage-based billing will later come from a usage_records table
- invoice numbers should use INV-YYYYMM-001 style

For each customer:

1. check subscriptions with due_date in a window from today - n days to today
2. for each due subscription, add a subscription charge as an invoice item
3. after adding that charge, move the subscription due_date forward by its billing interval
4. check extra users for the last billing period
5. add overage items for that period
6. if there is already an existing invoice you want to keep unchanged, create a new invoice instead of modifying the old one
7. if multiple subscriptions are due for the same customer during the run, they can all go onto one invoice

For each due subscription:

1. find its previous billing period
2. calculate usage in that period
3. create overage item only for that subscription and that previous period
4. do not duplicate overage for the same subscription-period pair

- does not allow recording usage for the rest of the already-billed interval.
- reject enter records for dates at or after that boundary
- a late-submission cutoff rule.