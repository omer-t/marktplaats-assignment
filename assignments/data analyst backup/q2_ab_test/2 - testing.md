# Context
> On testing: Marktplaats has decided on implementing a product feature that we think
will drive the number of Car ads with leads: How would you ideally set up the test
whether this initiative has improved this metric? 
> - Why do you choose this method?
> - What are the risks / challenges?
> - Use the dataset attached to examine the test groups:
>  - What is the result of your analysis?
>  - What insights did you gain?

# Answer

## Test Design
A randomized A/B test would be the appropriate framework to test this.

I would choose an A/B test because it gives the cleanest way to measure whether the feature caused a change in lead rate. Random assignment makes treatment and control ads comparable, so differences after the test are more likely to come from the feature. This is better than a before/after comparison, which can be affected by seasonality, market demand, or changes in ad supply.

### Business Question and Main KPI
Does the new product feature increase the number of car ads that receive *at least one lead*, without harming ad quality, buyer experience, or seller outcomes?
#### Primary metric definition
```sql
had_lead = telclicks > 0 OR bids > 0 OR n_asq > 0 OR webclicks > 0
```

This is the appropriate business question because:
1. The assignment phrasing was to "drive the number of car ads with leads", not to drive the number of leads.
2. Total/average leads may be more sensitive to outliers, driven by a few popular ads.

### Randomization Level
The key decision is what gets assigned to treatment or control: ads, sellers, or buyers.

| Unit | Use when | Main risk |
|---|---|---|
| Ad-level | The feature changes how a specific ad is shown or contacted, and does not strongly change seller behavior across ads | Treated ads may take leads from similar control ads* |
| Seller-level | The feature changes seller tools or listing quality | Fewer test units, so the test may need more time |
| Buyer-level | The feature changes search, browsing, recommendations, or other buyer-side experience | Harder to link the result back to specific ads |

*Example: if treatment and control ads compete for the same buyers, a treated ad may get a lead that would otherwise have gone to a control ad. This can make the feature look better than it really is for the marketplace overall.

For this case, I would start with ad-level randomization, because the dataset is at ad level and the goal is measured per ad.

I would still confirm how the groups were actually assigned before treating the result as causal.

### Treatment and Control
