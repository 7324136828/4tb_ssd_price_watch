# eBay API Compliance (`compliance.md`)

This file records how this repository uses the eBay API and why its production
keyset (`ebay-monitoring`) qualifies for the exemption from eBay's Marketplace
Account Deletion notifications.

## 1. The requirement

eBay requires every production keyset to do one of two things:

* **Option A — Exemption:** declare that the application stores no eBay user
  data, by turning on *Exempted from Marketplace Account Deletion* in the
  developer portal.
* **Option B — Subscription:** host a public HTTPS endpoint that answers
  eBay's challenge and deletes a user's data when eBay sends a deletion notice.

A keyset that does neither is marked non-compliant, and eBay can cut off its
API access.

## 2. Decision

**Option A, the exemption.** Reason to select in the portal: the application
does not persist eBay data.

Option B is not needed: with no eBay user data stored, a deletion endpoint
would have nothing to delete.

## 3. Why the exemption applies

The only code that calls eBay is `scripts/track_ebay.py`.

* **Public data only.** It calls the Browse API (`item_summary/search`) to
  find the cheapest Buy It Now listing of each tracked SSD, RAM module and
  MacBook.
* **Application token only.** It uses the client-credentials grant with the
  scope `https://api.ebay.com/oauth/api_scope`. No eBay user signs in, and no
  user token is requested or stored.
* **No user data is saved.** The script does not read or write seller
  usernames, feedback scores, buyer details, addresses or any other personal
  data.

What is saved for each eBay listing is one row in `prices.csv`:

| Column | Value for an eBay row |
|---|---|
| `date` | Run date |
| `category` | `ssd`, `ram` or `macbook` |
| `item` | The tracked product name from the script's own list |
| `spec` | Product spec (capacity, memory, flash type) |
| `store` | The fixed text `eBay` |
| `condition` | `new`, `used` or `refurbished` |
| `price_usd` | Listing price |
| `basis` | `direct` |
| `source_date` | Run date |
| `url` | `https://www.ebay.com/itm/<item id>` |

The listing title is used only to check that the listing matches the tracked
product; it is not saved. The item ID in the URL identifies a listing, not a
person.

GPU rows with store `eBay` come from `videocardprices.com` and `gpudeals.net`,
not from the eBay API, and hold the same columns.

## 4. Credentials

* `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` are read from the environment at
  run time.
* They are never written to this repository, to `prices.csv` or to logs.

## 5. When to revisit this

Switch to Option B, with a deletion endpoint, before making any change that
would store eBay user data. Examples:

* saving seller usernames, feedback or location with a price row;
* adding eBay user sign-in (a user token) for any feature;
* keeping raw API responses, which include seller details, on disk or in the
  repository.
