-- Interpretation
-- I count ads that were posted in May 2017, and check whether each ad received at least one lead within 24 hours after it was posted.

-- Assumptions
-- 1. Snowflake SQL syntax.
-- 2. Multiple lead events for the same ad count as one ad with leads.

with ads as (
    select
        seller_id,
        ad_id,
        category,
        -- Combine the date and time fields into one timestamp.
        timestamp_from_parts(ad_start_date, ad_start_time) as ad_start_ts
    from ad_table
    where ad_start_date >= '2017-05-01'
      and ad_start_date <  '2017-06-01'
),

lead_events as (
    select
        clsfd_seller_id as seller_id,
        clsfd_ad_id as ad_id,
        buyer_id,
        -- Combine the date and time fields into one timestamp.
        timestamp_from_parts(event_table.date, event_table.timestamp) as event_ts
    from event_table
    -- Lead event types.
    where eventtype in ('PHONE_CLICK', 'EMAIL', 'BID', 'URL_CLICK')
),

ad_level as (
    select
        ads.category,
        ads.seller_id,
        ads.ad_id,
        count(lead_events.ad_id) > 0 as had_lead_within_24h
    from ads
    left join lead_events
        on lead_events.ad_id = ads.ad_id
        -- Match on seller as well, in case ad_id is not unique across sellers.
       and lead_events.seller_id = ads.seller_id
       and lead_events.event_ts between ads.ad_start_ts and ads.ad_start_ts + interval '24 hours'
    group by
        ads.category,
        ads.seller_id,
        ads.ad_id
)

select
    category,
    count(*) as total_ads,
    count_if(had_lead_within_24h) as ads_with_leads_24h,
    count_if(had_lead_within_24h) / count(*) as share_ads_with_leads_24h
from ad_level
group by category
order by share_ads_with_leads_24h desc;
