# Everyday Hybrid Local-Cloud LLM Case Study Ideas

## Working Thesis

The most interesting everyday hybrid LLM applications are not just "small model
for cheap tasks, large model for hard tasks." They are privacy routers for
real life.

The local small language model (SLM) can safely inspect messy private context:
receipts, inbox exports, family calendars, photos, forms, household records,
device logs, and personal preferences. The cloud large language model (LLM) can
bring in fresh public knowledge: recall notices, policies, manuals, prices,
weather, transit, public forms, store pages, and current regulations.

The product value comes from the boundary:

```text
private life data -> local SLM -> sanitized task packet -> cloud LLM
                  <- local SLM verifies cloud output <- public-world answer
```

The cloud model should not be the place where the user's life is assembled. The
local model should assemble the private life context, redact it, ask only the
minimum outside-world question, and then verify the answer against the private
evidence before showing anything to the user.

Useful grounding references:

- Google Gemma 4 local agentic workflows:
  https://developers.googleblog.com/bringing-gemma-4-12b-to-your-laptop-unlocking-local-agentic-workflows-with-google-ai-edge/
- Gemma 4 model overview:
  https://ai.google.dev/gemma/docs/core
- ACM Queue on generative AI at the edge:
  https://queue.acm.org/detail.cfm?id=3733702
- Google Private AI Compute coverage:
  https://www.theverge.com/news/818364/google-private-ai-compute

## Idea 1: Receipt, Warranty, And Recall Guardian

### One-Line Pitch

A local-first assistant that watches your receipts, product documents, and
purchase emails, then finds recalls, expiring warranties, price protections,
return windows, and repair options without uploading your shopping history.

### Why It Is Interesting

Most people lose money through small household frictions: missed return windows,
forgotten warranties, unclaimed recalls, duplicate appliance purchases, and
repairable products thrown away too early. The private data is scattered across
email, PDFs, photos, scanned receipts, serial numbers, and product labels.

This is a strong hybrid use case because the local model needs to see intimate
purchasing history, while the cloud model is useful for public, fresh, and
dynamic information such as manufacturer policies, recall databases, and current
support pages.

### Local SLM Responsibilities

- Parse receipt images, PDFs, email confirmations, and product photos.
- Extract product names, model numbers, serial numbers, purchase dates, prices,
  store names, and warranty hints.
- Cluster duplicate evidence for the same item.
- Build a private inventory of owned items.
- Decide what can be safely sent outside the device.
- Redact names, full addresses, payment card fragments, order IDs, and unrelated
  basket items.
- Verify that any cloud-discovered recall or warranty policy actually matches
  the local product evidence.

### Cloud LLM Responsibilities

- Search or interpret public recall pages, manufacturer support pages, return
  policies, warranty terms, and price protection rules.
- Summarize complex support instructions.
- Compare candidate model numbers against public product variants.
- Draft a support email or claim script using a minimal data template.

### Example Workflow

```text
1. User drops a folder of receipts, product photos, and email exports.
2. Local SLM extracts a private household product graph.
3. Local SLM creates sanitized lookup tasks:
   - brand: "Contoso"
   - product category: "air fryer"
   - model candidate: "AF-4200"
   - purchase month: "2025-11"
   - no user name, order number, address, or card data
4. Cloud LLM checks recall, warranty, and return-policy sources.
5. Local SLM verifies the cloud result against the original receipt/photo.
6. User sees an evidence-linked action list.
```

### Possible Demo

Use synthetic receipts plus a few real public recall pages. Build a dashboard
with:

- "Money at risk" from expiring return windows or price protection.
- "Safety alerts" for recalled items.
- "Repair or replace" recommendation with evidence.
- Draft claim email with redaction preview.

### TDS Angle

"I built a local LLM that finds money hiding in my inbox without uploading my
inbox."

## Idea 2: Personal Bureaucracy Copilot

### One-Line Pitch

A local-first paperwork assistant for bills, insurance letters, lease documents,
government forms, school forms, and confusing notices.

### Why It Is Interesting

Everyday bureaucracy is one of the most painful domains for ordinary people.
The work is not conceptually glamorous, but it is high-value: understand the
notice, extract deadlines, identify missing documents, draft a response, and
avoid costly mistakes.

The user's documents are deeply private, but much of the required knowledge is
public: official instructions, form guidance, policy pages, agency checklists,
and appeal procedures.

### Local SLM Responsibilities

- Classify uploaded paperwork by type: bill, notice, lease clause, form,
  insurance explanation, appeal letter, school document, tax document.
- Extract key facts: deadline, amount, account type, required response,
  attachments, named parties, and risk level.
- Build a private task timeline.
- Redact personal identifiers and turn the private document into a generic
  question.
- Prepare draft responses using local evidence.
- Keep a local audit trail of which lines in the document support each claim.

### Cloud LLM Responsibilities

- Retrieve official guidance and public procedure pages.
- Explain generic form instructions.
- Compare the user's situation against public checklists after redaction.
- Help draft non-legal, non-medical administrative language.

### Example Workflow

```text
1. User uploads a confusing medical bill or utility notice.
2. Local SLM extracts dates, charges, required actions, and unknown terms.
3. Local SLM sends only a redacted procedural query to the cloud:
   "For a US utility billing dispute, what documents are usually needed?"
4. Cloud LLM returns a checklist and public source summary.
5. Local SLM maps the checklist back to the user's private documents.
6. User gets a packet:
   - what this notice means
   - what is due by when
   - what evidence is already available
   - what is missing
   - a draft response
```

### Possible Demo

Generate a synthetic stack of messy documents: a lease clause, a utility bill,
a school permission form, and an insurance explanation of benefits. Show how
the app turns them into a deadline board and response drafts.

### TDS Angle

"A hybrid LLM app for the paperwork nobody wants to do."

## Idea 3: Home Repair Detective

### One-Line Pitch

A multimodal home-repair assistant that uses local photos, appliance labels,
error codes, old invoices, and manuals to prepare a repair diagnosis packet
before calling a professional or attempting a safe DIY fix.

### Why It Is Interesting

Home repair is visually rich, stressful, and full of ambiguity. People often
send vague descriptions to repair providers: "my dishwasher is making a noise."
A local model can convert messy home evidence into structured observations
without exposing photos of the user's living space.

The cloud model is useful for public manuals, part numbers, common failure
modes, service bulletins, and rough cost estimates.

### Local SLM Responsibilities

- Interpret photos or short videos of the issue.
- Read appliance labels, error codes, LED patterns, breaker labels, water
  stains, cracks, filters, hoses, and installation context.
- Search local manuals or past invoices if the user provides them.
- Identify safety-sensitive situations that require human professional help.
- Redact room context and personal artifacts before external lookup.
- Verify whether cloud advice matches the exact observed model and symptoms.

### Cloud LLM Responsibilities

- Find public manuals, troubleshooting pages, compatible replacement parts, and
  common issue explanations.
- Compare public symptom descriptions with the sanitized symptom packet.
- Produce a checklist of safe observations to collect.
- Draft a concise message for a contractor.

### Example Workflow

```text
1. User photographs a washing machine error code and the model label.
2. Local SLM extracts:
   - brand and model
   - visible code
   - symptom description
   - installation observations
3. Cloud LLM checks public manuals and part guidance.
4. Local SLM confirms the manual applies to the visible model.
5. User receives:
   - likely causes
   - safe checks
   - do-not-attempt warnings
   - parts/tools likely needed
   - contractor message with evidence photos
```

### Possible Demo

Use a set of appliance-label photos, public manuals, and simulated symptoms.
Avoid dangerous DIY instructions. Focus on evidence collection and triage.

### TDS Angle

"Before calling a repair person, let a local multimodal model build the evidence
packet."

## Idea 4: Private Pantry And Grocery Optimizer

### One-Line Pitch

A private meal-planning assistant that sees pantry photos, dietary restrictions,
leftovers, family schedules, and budget constraints locally, then uses the cloud
only for prices, recalls, seasonal produce, and recipe inspiration.

### Why It Is Interesting

Most meal planners fail because they ignore the actual constraints: what is in
the fridge, what will expire soon, what the household refuses to eat, who is
home tonight, how much time is available, and what grocery prices look like now.

The local model owns the household context. The cloud model owns the public food
world.

### Local SLM Responsibilities

- Detect pantry/fridge items from photos and user corrections.
- Track expiration dates, leftovers, staple inventory, allergies, dislikes,
  nutrition goals, cooking equipment, and household schedule.
- Build meal constraints such as "20 minutes, no oven, use spinach today."
- Redact personal health and family context before cloud calls.
- Validate generated meal plans against actual inventory and restrictions.

### Cloud LLM Responsibilities

- Retrieve public recipes, substitutions, grocery prices, coupons, recall
  alerts, and seasonal availability.
- Suggest recipe candidates based on sanitized constraints.
- Explain nutrition or substitution ideas at a general level.

### Example Workflow

```text
1. User takes fridge and pantry photos.
2. Local SLM builds a private inventory and detects expiring items.
3. Local SLM sends a sanitized task:
   "Suggest dinners using spinach, eggs, rice, and canned tomatoes.
    No shellfish. 20 minutes. One pan."
4. Cloud LLM proposes options and current grocery add-ons.
5. Local SLM filters against local dislikes, allergies, and schedule.
6. User gets a shopping list and meal plan.
```

### Possible Demo

Use static pantry images, a local SQLite inventory, and a mock grocery-price API.
Show how different data-boundary choices change what leaves the device.

### TDS Angle

"A meal planner where the cloud never sees your family's eating habits."

## Idea 5: Family Logistics Air-Traffic Control

### One-Line Pitch

A household operations assistant that locally reads school emails, calendars,
forms, chore lists, family messages, and reminders, then asks the cloud only
about weather, traffic, public schedules, store hours, and event changes.

### Why It Is Interesting

Families do not need another chatbot. They need a daily operations brief that
turns scattered context into "what must happen today, who is responsible, and
what breaks if the outside world changes."

The data is intensely personal, but many dependencies are public.

### Local SLM Responsibilities

- Parse school emails, sports schedules, daycare notes, calendar events,
  permission slips, grocery needs, medication reminders, and household tasks.
- Resolve family-specific aliases and routines.
- Identify conflicts, missing forms, packing needs, and delegation options.
- Keep private family preferences and constraints local.
- Prepare sanitized public queries such as "weather near ZIP code at 4 PM" or
  "is library branch open this evening?"

### Cloud LLM Responsibilities

- Check weather, traffic, transit, school district pages, public event pages,
  store hours, and service disruptions.
- Summarize public changes that affect the private plan.

### Example Workflow

```text
1. Local SLM reads family calendar and school emails.
2. It detects:
   - soccer practice
   - permission slip due tomorrow
   - library book return
   - parent meeting overlap
3. Cloud LLM checks weather and public schedule changes.
4. Local SLM creates a morning brief:
   - pack cleats and rain jacket
   - sign form tonight
   - leave 15 minutes early
   - move grocery pickup
```

### Possible Demo

Generate a synthetic household inbox and calendar, then show daily briefs with
and without external weather/transit updates.

### TDS Angle

"A local-first family assistant that knows your life but only asks the cloud
about the world."

## Idea 6: Subscription And Spending Leak Finder

### One-Line Pitch

A private spending assistant that finds duplicate subscriptions, price hikes,
forgotten trials, unusual bills, and refund opportunities from local financial
exports and email receipts.

### Why It Is Interesting

This is small-money magic: not a grand financial advisor, but a practical tool
that saves attention and cash. The privacy boundary is obvious because bank
exports and email receipts should not be casually uploaded.

### Local SLM Responsibilities

- Parse CSV bank exports, app-store receipts, email confirmations, and bills.
- Cluster recurring charges by merchant and service.
- Detect price increases, duplicate subscriptions, inactivity hints, and
  suspicious changes.
- Redact account numbers, full transaction histories, and unrelated merchants.
- Prepare minimal cloud tasks: "Find cancellation policy for merchant X plan Y."

### Cloud LLM Responsibilities

- Find cancellation pages, refund policies, current public pricing, competitor
  alternatives, and support instructions.
- Draft concise cancellation or refund messages.

### Example Workflow

```text
1. User imports a bank CSV and receipt mailbox export.
2. Local SLM clusters recurring charges.
3. Local SLM identifies:
   - two music subscriptions
   - a trial that converted
   - a 30 percent price increase
4. Cloud LLM checks public cancellation/refund rules.
5. Local SLM produces an action list ranked by likely savings.
```

### Possible Demo

Use synthetic bank data and public subscription-policy pages. Show the local
redaction envelope before each cloud query.

### TDS Angle

"A private AI accountant for small money leaks."

## Idea 7: Apartment Hunting Copilot

### One-Line Pitch

A hybrid apartment search assistant that keeps salary, debt comfort, commute
tolerance, accessibility needs, pets, relationship constraints, and personal
dealbreakers local while using the cloud for listings and neighborhood data.

### Why It Is Interesting

Apartment search is emotionally exhausting because search filters do not capture
real tradeoffs. A listing is not just "2 bedrooms under $2,500"; it is commute,
noise, safety perception, pet rules, flood risk, sunlight, laundry, landlord
reviews, deposits, and life logistics.

### Local SLM Responsibilities

- Maintain the user's private preference model.
- Parse lease PDFs, screenshots, listing notes, and personal budget constraints.
- Score tradeoffs locally.
- Redact sensitive financial and household details.
- Verify that cloud-discovered listing claims match the actual listing text.

### Cloud LLM Responsibilities

- Search or summarize listing pages, transit routes, local ordinances, flood
  maps, market comps, neighborhood pages, and reviews.
- Explain public lease terms or tenant-rights resources in generic language.

### Example Workflow

```text
1. User defines private constraints locally.
2. Cloud LLM collects candidate listings and public neighborhood facts.
3. Local SLM scores each listing against private constraints.
4. User receives:
   - fit score
   - hidden tradeoffs
   - questions to ask the landlord
   - red flags
   - viewing checklist
```

### Possible Demo

Use public listing-like mock data plus transit and neighborhood summaries. The
article can focus on ranking methodology and privacy-preserving preference
matching.

### TDS Angle

"Why apartment search is a perfect hybrid LLM problem."

## Idea 8: Caregiver Memory Binder

### One-Line Pitch

A local AI binder for caregivers that organizes medications, symptoms,
appointments, discharge documents, lab reports, food/sleep notes, and questions
for clinicians while using the cloud only for public appointment-prep and
logistics resources.

### Why It Is Interesting

Caregiving is coordination-heavy and emotionally draining. The problem is often
not "diagnose the patient"; it is "what happened, when, what changed, what do we
need to ask, and what documents should we bring?"

This must be framed carefully as organization and preparation, not medical
diagnosis.

### Local SLM Responsibilities

- Build a private timeline from notes, documents, medications, symptoms, and
  appointments.
- Extract questions and unresolved concerns.
- Summarize changes since the last appointment.
- Detect missing information such as dosage, dates, or follow-up instructions.
- Redact all protected or identifying information before external lookups.
- Keep a source-linked binder for the caregiver.

### Cloud LLM Responsibilities

- Retrieve general appointment-prep templates, public medication information,
  insurance/provider logistics, and non-diagnostic educational resources.
- Help turn a private timeline into a concise doctor-visit agenda after local
  redaction.

### Example Workflow

```text
1. Caregiver adds notes, appointment PDFs, and medication photos.
2. Local SLM creates a timeline and flags missing facts.
3. Cloud LLM retrieves generic preparation guidance.
4. Local SLM creates:
   - one-page visit summary
   - question list
   - medication change log
   - documents to bring
```

### Possible Demo

Use fully synthetic health/caregiving data. Add explicit safety guardrails:
organization only, no diagnosis, no treatment instructions, human clinician in
the loop.

### TDS Angle

"A local AI binder for caregiving, where the sensitive timeline stays on your
machine."

## Idea 9: Personal Climate And Home Energy Coach

### One-Line Pitch

A home-energy assistant that locally analyzes smart-meter data, thermostat
history, room temperatures, EV charging, occupancy patterns, and comfort
preferences, then uses the cloud for weather, electricity tariffs, outage
alerts, rebates, and appliance-efficiency references.

### Why It Is Interesting

Home energy is a good everyday hybrid problem because local behavior patterns
are private, while outside constraints change constantly. The app can turn raw
energy data into practical actions instead of generic advice.

### Local SLM Responsibilities

- Parse smart-meter exports, thermostat logs, appliance notes, EV charging
  schedules, and occupancy preferences.
- Detect anomalous usage patterns.
- Build a comfort-aware local profile.
- Avoid exposing household routines.
- Validate cloud suggestions against actual household constraints.

### Cloud LLM Responsibilities

- Retrieve weather forecasts, peak-price windows, local rebate programs,
  appliance-efficiency references, outage alerts, and public utility guidance.
- Summarize time-sensitive recommendations.

### Example Workflow

```text
1. User imports meter and thermostat history.
2. Local SLM learns comfort and usage patterns.
3. Cloud LLM checks tomorrow's heat wave and tariff windows.
4. Local SLM recommends:
   - pre-cool before peak pricing
   - delay EV charging
   - run dishwasher after 9 PM
   - investigate abnormal appliance draw
```

### Possible Demo

Use public sample energy data, weather API data, and simulated tariff windows.
Show before/after plans and privacy envelopes.

### TDS Angle

"A hybrid LLM that turns home energy data into actual decisions."

## Idea 10: Private Life Memory Analyst

### One-Line Pitch

A local personal-memory analyst that indexes calendar entries, notes, journals,
photos, task history, and personal reflections, then uses the cloud only for
non-sensitive public context such as places, events, weather history, books,
movies, or routes.

### Why It Is Interesting

This is the most personal and reflective idea. The value is not automation but
self-understanding: patterns in attention, relationships, commitments, energy,
and postponed intentions.

It must be designed with restraint. The product should help the user see their
own patterns, not manipulate them or over-pathologize ordinary life.

### Local SLM Responsibilities

- Index personal notes, calendar events, photos, and task history.
- Answer memory questions using local evidence.
- Detect recurring themes, postponed tasks, overloaded weeks, and positive
  patterns.
- Keep embeddings, notes, and summaries local.
- Decide when public context would help and redact aggressively.

### Cloud LLM Responsibilities

- Fill in public context: place information, event descriptions, weather
  history, public holidays, book/movie metadata, travel routes.
- Help produce polished reflective summaries after local filtering.

### Example Workflow

```text
1. User asks, "What made my good weeks different from bad weeks?"
2. Local SLM analyzes calendar, notes, and task completion patterns.
3. Cloud LLM is used only for public context, if needed:
   - holidays
   - travel disruption
   - event metadata
4. Local SLM produces a source-linked private reflection.
```

### Possible Demo

Use a synthetic personal dataset: calendar, notes, photos metadata, and tasks.
The app can answer questions about routines without exposing the dataset.

### TDS Angle

"A local LLM as a private life observatory."

## Recurring SLM-LLM Collaboration Patterns

### Pattern 1: Local SLM As Privacy Firewall

The local model is the first reader of private context. It extracts facts,
classifies documents, removes irrelevant details, redacts identifiers, and
decides whether cloud help is justified.

This pattern appears in every idea above. The SLM is not "the weaker model"; it
is the trust boundary.

### Pattern 2: Local SLM As Context Compressor

Private life data is noisy: images, emails, notes, receipts, forms, logs, and
calendar entries. The local SLM compresses that mess into a structured envelope
the cloud can understand.

Example envelope:

```json
{
  "task": "public_policy_lookup",
  "domain": "product_recall",
  "safe_facts": {
    "brand": "ExampleBrand",
    "model": "AB-123",
    "product_type": "air fryer",
    "purchase_month": "2025-11"
  },
  "excluded_fields": [
    "name",
    "address",
    "order_id",
    "full_receipt",
    "payment_details"
  ]
}
```

### Pattern 3: Cloud LLM As Public-World Interface

The cloud model is best used for things that are public, fresh, distributed, or
too broad for a local model to know reliably:

- recall notices
- policy pages
- manuals
- public forms
- weather and transit
- prices and availability
- tariffs and rebates
- neighborhood information
- public health or appointment-prep guidance

The cloud model should be given a task packet, not a diary.

### Pattern 4: Local SLM As Verifier And Grounder

After the cloud responds, the local SLM checks whether the answer actually
matches the private evidence.

Examples:

- Does the recall apply to this exact model number?
- Does the warranty policy match the purchase date?
- Does the repair manual match the visible appliance label?
- Does the meal plan violate an allergy or dislike?
- Does the apartment recommendation violate a private budget constraint?

This creates a useful collaboration loop:

```text
SLM extracts -> LLM retrieves/reasons -> SLM verifies -> human approves
```

### Pattern 5: SLM-First, LLM-On-Demand Routing

Most user queries should not go to the cloud. The local model should answer
locally when the answer is inside the private dataset or when cloud freshness is
not needed.

Cloud escalation should happen only when:

- current public data is required
- the local model lacks confidence
- a policy/manual/listing/source needs retrieval
- the user explicitly approves external lookup
- the task benefits from stronger reasoning over sanitized facts

### Pattern 6: Human-Visible Redaction

For trust, the app should show users what will leave the device before the cloud
call. This is especially important for everyday-life tools because people may
not understand invisible privacy claims.

Good UI primitive:

```text
About to ask the cloud:
"Find recall and warranty information for ExampleBrand AB-123 air fryer,
purchased around November 2025."

Not shared:
your name, address, full receipt, payment details, order number, other items.
```

### Pattern 7: Local Memory, Cloud Statelessness

The local side should maintain long-term personal memory. The cloud side should
receive temporary, task-scoped prompts. This avoids rebuilding the user's life
in a cloud account.

### Pattern 8: Dual-Model Disagreement As Product Signal

The two models can intentionally disagree:

- Local SLM: "The cloud found a recall, but the serial range does not match."
- Local SLM: "This recipe satisfies the public constraints but violates your
  local dislike profile."
- Local SLM: "This apartment looks good publicly, but your commute constraint
  fails."

Disagreement is not a bug. It is a way to expose the boundary between public
general advice and private fit.

### Pattern 9: Cloud For Breadth, Local For Fit

This is the most compact pattern:

```text
Cloud finds possibilities.
Local decides whether they fit this person.
```

This applies to meals, apartments, subscriptions, repairs, forms, purchases,
caregiving, and energy.

### Pattern 10: Actions Are Local Drafts, Not Cloud Commands

For everyday tools, the cloud should not directly send emails, cancel plans,
submit forms, or contact support. The cloud may help draft. The local app should
stage the action, attach evidence, and ask for human approval.

## What Is Still Missing

### Missing 1: A Permission Model People Can Understand

The hardest design problem is not the model call. It is permissions.

Users need controls like:

- This app may read only this folder.
- This app may inspect receipts but not full emails.
- This app may ask the cloud about product recalls but not upload images.
- This app may draft an email but not send it.
- This app may remember product inventory but forget grocery photos after use.

For a TDS post, a concrete permission model would make the article much more
serious.

### Missing 2: A Standard "Sanitized Task Packet" Format

The hybrid architecture needs a structured boundary object. Without it, the
design becomes vague. A useful case study should define a small schema:

- task type
- allowed facts
- excluded facts
- source evidence IDs
- risk level
- cloud tools allowed
- user approval state
- expiration time

This would make the article feel architectural rather than anecdotal.

### Missing 3: Evaluation Metrics Beyond Accuracy

Everyday hybrid systems need metrics such as:

- private fields leaked per cloud call
- number of unnecessary cloud calls avoided
- recall of actionable opportunities
- false-positive burden on the user
- evidence coverage
- time saved
- money saved
- user trust after seeing redaction previews

Accuracy alone is too narrow.

### Missing 4: Failure Modes And Guardrails

The strongest post should show where the pattern fails:

- local model extracts the wrong model number
- cloud finds an outdated policy
- cloud result applies to a similar but different product
- local verifier misses a conflict
- redaction removes too much context
- user over-trusts an administrative or health-related suggestion

The article should include at least one deliberate failure demo.

### Missing 5: A Human-In-The-Loop Action Layer

Many of these ideas become useful only when the app can help the user act:

- send a support email
- create a calendar reminder
- generate a contractor message
- fill a checklist
- open a cancellation page
- prepare documents for an appointment

But action must be staged locally with evidence and approval. The post should
show an "action review" screen, not just a chatbot answer.

### Missing 6: Data Lifecycle Design

Everyday context is sensitive. The app should define:

- what is stored permanently
- what is stored temporarily
- what is embedded
- what is deleted after task completion
- what is exported
- what is never indexed

This is especially important for caregiving, family logistics, finances, and
personal memory.

### Missing 7: Non-Text Interfaces

Everyday use is often not text-first. The best demos should include at least
one of:

- photo capture
- voice note
- document scan
- calendar import
- receipt OCR
- local notification
- redaction preview

Hybrid LLM architecture becomes more compelling when it handles real input
messiness.

### Missing 8: A Clear Winner Case Study

The strongest candidates for a first TDS article are:

1. Receipt, Warranty, And Recall Guardian
2. Home Repair Detective
3. Personal Bureaucracy Copilot

They have the best combination of everyday usefulness, clear privacy boundary,
cloud usefulness, visible demo value, and limited safety risk.

Caregiver Memory Binder is emotionally powerful, but needs careful safety
framing. Private Life Memory Analyst is poetic, but may be harder to evaluate.
Family Logistics is useful, but requires many integrations to feel real.

## Recommended Article Direction

If the goal is one memorable and buildable TDS post, the best direction is:

### "The Cloud Never Saw My Receipts: Building a Hybrid Local-Cloud Warranty And Recall Guardian"

Why this is the strongest:

- Easy for readers to understand.
- Practical ROI: money saved and safety alerts.
- Strong privacy story: receipts and emails stay local.
- Natural cloud role: recalls, manuals, warranty policies, support pages.
- Multimodal enough to be interesting: receipt images, product photos, PDFs,
  emails.
- Low-risk compared with medical, legal, or financial advice.
- Evaluation is concrete: model-number extraction, recall matching, redaction
  quality, cloud-call minimization, and actionable findings.

Core architecture:

```text
Local ingestion:
  receipt images, emails, product photos, PDFs

Local Gemma:
  OCR cleanup, product extraction, clustering, redaction, task packet creation

Cloud LLM:
  public recall/warranty/manual lookup and summarization

Local Gemma:
  verify match, rank actions, draft claim, show evidence

Human:
  approve action, export packet, set reminder
```

The big idea:

> In consumer AI, hybrid local-cloud design is not a deployment choice. It is a
> privacy contract.
