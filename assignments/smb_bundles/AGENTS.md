# SMB Bundles Assignment

## Assignment Goal

Complete the SMB Bundle Strategy case in presentation form.

The final work should be based on analysis in the four question-specific notebooks. Keep the notebooks easy to copy into Google Slides:

- Use short, simple Markdown text.
- Prefer bullets over long paragraphs.
- Make every section presentation-ready.
- Put the conclusion before detailed evidence where useful.
- Use clear chart titles and concise axis labels.
- Avoid overly technical notebook narration unless it explains a decision.

## File Map

Assignment folder:

- `assignments/smb_bundles/q1_identify.ipynb`
  - Notebook for Question 1.
  - Use this for SMB seller identification logic based on the available schemas and assignment context.
- `assignments/smb_bundles/q2_prioritize.ipynb`
  - Notebook for Question 2.
  - Use this for outreach prioritization analysis using `data/q2_prioritize.csv`.
- `assignments/smb_bundles/q3_monitor.ipynb`
  - Notebook for Question 3.
  - Use this for bundle monitoring, dashboard metrics, and sales impact analysis using `data/q3_monitor.csv`.
- `assignments/smb_bundles/q4_scale.ipynb`
  - Notebook for Question 4.
  - Use this for the conceptual marketing campaign proposal based on Q1-Q3 findings and relevant platform context.
- `assignments/smb_bundles/functions.py`
  - Shared helper functions for all SMB Bundles notebooks.
  - Use this for repeatable mechanics such as paths, data loading, metric creation, aggregation, formatting, and plotting setup.
- `assignments/smb_bundles/docs/Business Case for BA 2026 - SMB Bundles.pdf`
  - Assignment brief and questions.
  - Contains all 4 assignment questions.
  - Read this first and use it as the source of truth for required outputs.
- `assignments/smb_bundles/data/Marktplaats2dehands Business Analytics SMB Dataset.xlsx`
  - Workbook with all provided datasets for this assignment.
  - Original source file. Do not alter this file.
  - Contains 3 sheets:
    - `Question 1`: table schemas / available data fields for Q1.
    - `Question 2`: dataset for Q2.
    - `Question 3`: dataset for Q3.
  - There is no dedicated dataset or schema for Q4.
- `assignments/smb_bundles/data/q2_prioritize.csv`
  - CSV export of the `Question 2` sheet.
  - Use this as the main analysis input for Q2.
- `assignments/smb_bundles/data/q3_monitor.csv`
  - CSV export of the `Question 3` sheet.
  - Use this as the main analysis input for Q3.

## Assignment Questions

The PDF contains all assignment questions and asks for a 25-minute presentation covering four questions. Use this naming convention:

1. SMB Identification: Identify
2. Outreach Prioritization: Prioritize
3. Sales Dashboard: Monitor
4. Marketing Campaign: Scale

The expected audience is both analysts and business partners. Balance analytical rigor with clear business recommendations.

## Business Context

Adevinta BNL consists of Marktplaats and 2dehands/2ememain, the largest classifieds platforms in the Dutch and Belgian markets.

Context from the assignment:

- The platforms facilitate trade for millions of users.
- They average about 400,000 new listings per day.
- They actively serve almost 100,000 SMB sellers.
- SMB sellers are currently served through two propositions that are not aligned or jointly offered.

Current SMB seller propositions:

- Pro:
  - pay-per-click proposition
  - sellers pay CPC when their ads are clicked
  - CPC is usually 1-4 cents
  - sellers can set CPC bids for more visibility
  - often used by sellers with their own web shop
  - ads are listed through the Pro console
  - important revenue stream
- SYI, short for Sell-Your-Item:
  - regular ad listing flow through app or website
  - used by both business sellers and consumers
  - some categories require insertion fees
  - sellers can buy paid features for more visibility

Important analytical framing:

- Pro and SYI data sit in separate places in the data warehouse.
- The current split can create a false churn view.
- Example: a seller moving from Pro to SYI might look churned to the Pro team, even though they are still active on the platform.
- The assignment is partly about creating a better cross-proposition view of SMB sellers.

The assignment opening text says to use:

- the provided data
- business acumen
- what can be found on the Marktplaats platform
- potentially external research

Use Marktplaats platform information where applicable, especially for proposition details, seller pages, bundle visibility examples, category context, and marketing/channel ideas. Treat platform observations as supporting context and keep the core recommendations grounded in the provided assignment data.

## Data Map

Workbook: `data/Marktplaats2dehands Business Analytics SMB Dataset.xlsx`

The Excel workbook is the original source file and should not be modified.

The workbook contains 3 sheets only:

- `Question 1`: table schemas / available data fields for Q1.
- `Question 2`: dataset for Q2.
- `Question 3`: dataset for Q3.

There is no separate dataset for Q4. Answer Q4 conceptually, using the business context and findings from Q1-Q3.

CSV analysis copies:

- `data/q2_prioritize.csv`
  - exported from workbook sheet `Question 2`
  - 129,501 data rows
  - 18 columns
- `data/q3_monitor.csv`
  - exported from workbook sheet `Question 3`
  - 8,830 data rows
  - 5 columns

Use the CSV files for notebook analysis where possible. Use the Excel file only as the original source/reference, especially for Q1 schemas.

## Notebook Files

The assignment is split into four notebooks:

- `q1_identify.ipynb`
- `q2_prioritize.ipynb`
- `q3_monitor.ipynb`
- `q4_scale.ipynb`

Each notebook starts with:

- a main title
- an `Assignment` sub-header
- a Markdown blockquote containing the question text copied from the PDF

Do not alter the main title or the `Assignment` section in these notebooks unless the user specifically asks for that change. Add analysis, assumptions, code, charts, and conclusions below the existing assignment prompt.

## Shared Helpers

Use `functions.py` as the shared helper module for all notebooks in this assignment.

Keep notebooks readable and presentation-oriented:

- Put reusable mechanics in `functions.py`.
- Keep notebook code cells short.
- Keep notebook Markdown focused on assumptions, findings, and recommendations.
- Avoid repeating the same loading, cleaning, aggregation, formatting, or plotting code across notebooks.

`functions.py` should stay general enough to be reused across questions and future analysis:

- file paths and constants
- Q2 and Q3 data loading
- seller-level aggregations
- subscription and dashboard metrics
- simple prioritization helpers
- reusable formatting helpers
- reusable chart setup and labeling helpers

Document helper functions where the purpose or assumptions are not obvious. Prefer clear function names and short docstrings over long notebook comments.

### Sheet: `Question 1`

This is a data dictionary, not a normal analysis table. It describes available fields for identifying SMB sellers.

Available information includes:

- User information:
  - user id
  - email address
  - postal code
  - bank account checked
  - corporate bank account flag
  - notification opt-ins
  - registration date/time
  - reviews
  - seller description
  - seller photo flag
- Ad information:
  - ad id
  - seller user id
  - ad start/end date
  - title
  - asking price
  - attributes
  - category
  - placement platform/device
  - postal code
  - number of photos
  - messaging/chat flag
  - phone number shown flag
  - external URL flag
  - insertion fee
- Feature information:
  - feature id
  - ad id
  - feature type
  - feature start/end date
  - feature fee
- Messaging information:
  - message id
  - ad id
  - seller id
  - buyer id
  - message direction
  - message date/time
  - message contents are not available
- Traffic information:
  - page type
  - click/action type
  - logged-in user id where available
  - A/B experiment exposure flag
  - page-specific dimensions
  - can be used for buyer and seller behavior, leads, and seller actions before/after listing
- Pro information:
  - ad id
  - seller user id
  - ad start/end date
  - title
  - asking price
  - attributes
  - category
  - postal code
  - number of photos
  - messaging/chat flag
  - phone number shown flag
  - external URL flag
  - CPC
  - daily impressions
  - daily clicks
  - daily URL clicks
- Pro invoicing:
  - user id
  - invoice month
  - total costs
  - discount
  - VAT
  - total invoice amount
  - invoice sent date
  - invoice paid date

Also includes reference lists for:

- level 1 categories
- feature types

Use this sheet to propose 3-8 SMB identifiers. Good identifiers should combine multiple behavioral signals, not rely on only one field.

### Sheet: `Question 2`

Monthly usage statistics per seller, category, and month for identified SYI prospects.

Shape observed:

- 129,501 data rows in the CSV export
- 18 columns
- period: 2023-2024

Columns:

- `USER_ID`
- `FTR_MONTH`
- `CATEGORY_NAME`
- `N_FREE_AD_INSERTIONS`
- `N_PAID_AD_INSERTIONS`
- `FEE_PAID_AD_INSERTIONS`
- `N_AD_RENEWALS`
- `FEE_AD_RENEWALS`
- `N_DAGTOPPERS`
- `FEE_DAGTOPPERS`
- `N_HOMEPAGE`
- `FEE_HOMEPAGE`
- `N_PAID_URL`
- `FEE_PAID_URL`
- `N_AD_UPCALLS`
- `FEE_AD_UPCALLS`
- `N_URGENCY`
- `FEE_URGENCY`

Use `data/q2_prioritize.csv` to recommend which sellers to call first from the 80k identified prospects, using the 5% sample.

Useful analysis directions:

- Aggregate from row level to seller level.
- Create total ads, paid ads, total feature usage, total fees, active months, category breadth, recent activity, and trend metrics.
- Compare heavy, medium, and light sellers.
- Identify sellers already paying for visibility as likely high-intent prospects.
- Consider bundle fit:
  - Basic for sellers with meaningful volume but lower current feature spend.
  - Plus for sellers with high feature usage, strong paid visibility behavior, many ads, or broad category activity.
- Recommend a clear prioritization score that can rank sellers.
- Explain why the top segment is worth calling.

### Sheet: `Question 3`

Bundle registration data after launch.

Shape observed:

- 8,830 data rows in the CSV export
- 5 columns

Columns:

- `User ID`
- `Customer type`
- `Bundle`
- `Start`
- `End`

Notes from the PDF:

- First 28 days are free as a launch promotion.
- Basic price: EUR 19.99 per 4 weeks.
- Plus price: EUR 49.99 per 4 weeks.
- Every seller can receive the discount only once.
- Sellers can stop or switch at any point.
- For this case, assume immediate payment for the full 4 weeks after the free period.
- Do not refund previous bundle time when a seller switches.
- `2099-12-31` appears to represent still-active subscriptions.

Use `data/q3_monitor.csv` to design and partially populate a sales monitoring dashboard.

Useful dashboard metrics:

- total registrations
- active subscriptions
- new registrations by week or month
- Basic vs Plus mix
- SYI vs Pro mix
- free-trial cohort conversion
- paid subscriptions after the first 28 days
- estimated revenue
- churn or ended subscriptions
- upgrades and downgrades where visible
- retention by cohort

Clearly separate:

- metrics that can be calculated from the provided sheet
- metrics that need extra data, such as outreach call logs, impressions, seller performance, bundle page traffic, campaign spend, or CRM status

## Notebook Workflow

Use the four question-specific notebooks as the main working artifacts.

Recommended notebook structure:

1. `Setup`
   - Import libraries.
   - Set plotting style.
   - Import `functions.py` as the shared helper module.
   - Use paths and constants from `functions.py`.
2. `Question 1 - SMB seller identifiers`
   - Summarize proposed identifiers in bullets.
   - Explain why each signal indicates business intent.
   - Mention risks and false positives.
3. `Question 2 - Outreach prioritization`
   - Load `data/q2_prioritize.csv` through `functions.py`.
   - Clean column names if helpful.
   - Aggregate to seller level using shared helper functions where possible.
   - Build exploratory charts.
   - Create a simple prioritization score.
   - Recommend top seller segments and bundle offers.
4. `Question 3 - Sales dashboard`
   - Load `data/q3_monitor.csv` through `functions.py`.
   - Calculate launch and subscription metrics using shared helper functions where possible.
   - Draft dashboard sections and visual examples.
   - List missing data needed for a complete dashboard.
5. `Question 4 - Marketing campaign`
   - Propose one campaign.
   - Include target audience, channels, message, and KPIs.
   - Tie campaign logic back to Q1-Q3 insights.
   - Do not look for a separate Q4 dataset; none is provided.
6. `Slide outline`
   - End with a concise suggested presentation flow.

## Analysis Standards

- Keep assumptions explicit.
- Prefer simple, explainable scoring over complex modeling.
- Use business-friendly language.
- Use relevant Marktplaats platform observations where they improve the answer.
- Do not overfit the 5% sample.
- Call out limitations when the data cannot answer something directly.
- Use EUR formatting for revenue.
- Treat dates carefully:
  - Q1 context is December 2024.
  - Q2 launch context is March 2025.
  - Q3 is after launch.

## Presentation Style

Write notebook Markdown as if it will become slides:

- Start sections with the key message.
- Use 3-5 bullets per insight.
- Keep bullets short.
- Use plain language, for example:
  - "These sellers already pay for visibility."
  - "Plus is best for sellers with high feature usage."
  - "Basic is a low-friction first step for active but lower-spend sellers."
- Include chart captions that explain the takeaway, not just the metric.

## Deliverable Expectations

The notebook should support a 25-minute presentation with:

- A clear SMB identification logic.
- A ranked outreach recommendation for the first 20k sellers.
- A bundle recommendation by seller segment.
- A dashboard concept with calculated example metrics.
- One concrete marketing campaign proposal.
- A short list of assumptions, limitations, and additional data needs.
