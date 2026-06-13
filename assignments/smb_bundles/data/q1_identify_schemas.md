# Question 1 Schemas

Source workbook: `Marktplaats2dehands Business Analytics SMB Dataset.xlsx`, sheet `Question 1`.

The sheet describes the data available for identifying likely SMB sellers as of December 2024. Data coverage goes three years back.

## User Related Info

| Field | Original comment |
| --- | --- |
| User id |  |
| Email address |  |
| Postal code | Not mandatory |
| Bank account checked | Not mandatory; used for payments |
| Bank account is corporate y/n | Not mandatory |
| Notification opt ins | To receive updates through app or email, marketing outings, and/or tips & tricks |
| Registration date/time |  |
| Reviews | Reviews a user has received from other users after trading with them |
| Seller description | Introductory statement about the seller, not mandatory |
| Seller photo y/n | Profile picture, not mandatory |

## Ad Related Info

| Field | Original comment |
| --- | --- |
| Ad id |  |
| User id | Of the seller |
| Ad start date/time |  |
| Ad end date/time |  |
| Ad title |  |
| Ad asking price |  |
| Ad attributes | Attributes, such as Color = Blue, Table width = 200cm, Brand = Ralph Lauren |
| Ad category | Both level 1 and level 2 in the category hierarchy; level 1 is shown below |
| Ad placement platform | Desktop, iOS, Android |
| Ad placement device | Web, smartphone, tablet, ... |
| Postal code | Not mandatory |
| Number of photos |  |
| Open for messaging or chat y/n |  |
| Phone number shown y/n |  |
| External URL attached to the ad y/n |  |
| Insertion fee | If applicable |

## Feature Related Info

| Field | Original comment |
| --- | --- |
| Feature id |  |
| Ad id | On which the feature is bought. The source sheet labels this as `Ad if`, likely a typo for `Ad id`. |
| Feature type |  |
| Feature start date/time |  |
| Feature end date/time |  |
| Feature fee | If applicable |

## Messaging

| Field | Original comment |
| --- | --- |
| Message id |  |
| Ad id |  |
| Seller id |  |
| Buyer id |  |
| Message direction |  |
| Message date/time |  |
| Message contents | Contents of the messages cannot be seen. |

## Traffic Info

For every hit on the website, the following information is known.

| Field | Original comment |
| --- | --- |
| Page | Result page, homepage, specific ad, ... |
| Click | Do a search, view an ad, click on a phone number, place a bid, ... |
| User id | If the user is logged in |
| Exposed to an A/B experiment y/n |  |
| Specific dimensions per page type |  |

Traffic info can be used to determine both seller and buyer behavior. It can support metrics such as number of leads on an ad and what a seller did before or after listing an ad.

## Pro Info

| Field | Original comment |
| --- | --- |
| Ad id |  |
| User id | Of the seller |
| Ad start date/time |  |
| Ad end date/time |  |
| Ad title |  |
| Ad asking price |  |
| Ad attributes | Attributes, such as Color = Blue, Table width = 200cm, Brand = Ralph Lauren |
| Ad category | Both level 1 and level 2 in the ad hierarchy; level 1 is shown below |
| Postal code | Not mandatory |
| Number of photos |  |
| Open for messaging or chat y/n |  |
| Phone number shown y/n |  |
| External URL attached to the ad y/n |  |
| CPC | Cost per click, set by seller |
| Daily number of impressions | Number of times the ad is shown in results |
| Daily number of clicks | Number of times the ad has been clicked |
| Daily number of URL clicks | Number of times the external URL in the ad has been clicked |

## Pro Invoicing Info

| Field | Original comment |
| --- | --- |
| User id |  |
| Invoice month |  |
| Total costs |  |
| Discount | If applicable |
| VAT |  |
| Total invoice amount |  |
| Invoice sent date/time |  |
| Invoice paid date/time | If applicable |

## Reference: Categories

| Category id | Category name (Dutch) | Category name (English) |
| ---: | --- | --- |
| 1 | Antiek en Kunst | Antiques and Art |
| 31 | Audio, Tv en Foto | Audio, TV and Photo |
| 48 | Auto diversen | Miscellaneous Cars |
| 91 | Auto's | Cars |
| 167 | Vacatures | Jobs |
| 201 | Boeken | Books |
| 239 | Doe-het-zelf en Verbouw | DIY and Renovation |
| 289 | Caravans en Kamperen | Caravans and Camping |
| 322 | Computers en Software | Computers and Software |
| 356 | Spelcomputers en Games | Game Consoles and Games |
| 378 | Contacten en Berichten | Contacts and Messages |
| 395 | Dieren en Toebehoren | Animals and Accessories |
| 428 | Diversen | Miscellaneous |
| 445 | Fietsen en Brommers | Bicycles and Mopeds |
| 504 | Huis en Inrichting | Home and Furnishings |
| 537 | Witgoed en Apparatuur | White Goods and Appliances |
| 565 | Kinderen en Baby's | Children and Babies |
| 621 | Kleding \| Dames | Clothing \| Women |
| 678 | Motoren | Motorcycles |
| 728 | Muziek en Instrumenten | Music and Instruments |
| 784 | Sport en Fitness | Sports and Fitness |
| 820 | Telecommunicatie | Telecommunications |
| 856 | Vakantie | Vacation |
| 895 | Verzamelen | Collectibles |
| 976 | Watersport en Boten | Water Sports and Boats |
| 999 | Woningen \| Huur | Homes \| Rental |
| 1032 | Huizen en Kamers | Houses and Rooms |
| 1085 | Zakelijke goederen | Business Goods |
| 1098 | Diensten en Vakmensen | Services and Tradespeople |
| 1099 | Hobby en Vrije tijd | Hobby and Leisure |
| 1744 | Cd's en Dvd's | CDs and DVDs |
| 1776 | Kleding \| Heren | Clothing \| Men |
| 1784 | Postzegels en Munten | Stamps and Coins |
| 1826 | Sieraden, Tassen en Uiterlijk | Jewelry, Bags and Appearance |
| 1847 | Tuin en Terras | Garden and Terrace |
| 1984 | Tickets en Kaartjes | Tickets |
| 2600 | Auto-onderdelen | Car Parts |

## Reference: Feature Types

| Feature type | Description |
| --- | --- |
| 1 day dagtopper | Ad is put on top of the results for one day. |
| 3 day dagtopper | Ad is put on top of the results for three days. |
| 7 day dagtopper | Ad is put on top of the results for seven days. |
| Homepage feature | Ad is featured on the homepage. |
| Paid URL | Ad can include a link to an external website. |
| Upcall | Ad lifetime is reset, so that the ad is put back on top of the results. |
| Urgency feature | Ad shows an indication that it needs to be sold with urgency. |
| Marktplaats Extra | Monthly extra visibility for all ads through larger pictures and "more from this seller". |
