# Retail portfolio planner

Three small tools for running a store investment portfolio the way a Retail Development leader has to: more candidate stores than capital or delivery capacity can support, every business case built the same way, and a quarterly review that holds the portfolio to plan. Built by Zubair Sohail with Claude as a coding partner. **All data is illustrative or public. Nothing here is drawn from any employer's confidential information.**

The thread through all three is a point of view on where AI belongs in a planning function: the computer does the arithmetic and drafts the words, AI is the coding partner that makes small, sharp tools cheap to build, and a named person always owns the judgment. AI never invents a number. The three tools share one set of numbers — the store economics model feeds the prioritiser, so the ranking and the business case can never disagree.

## 1. Store investment prioritiser

The portfolio problem: a list of candidate stores whose combined capital ask exceeds the budget, and whose combined build exceeds the delivery slots. This tool decides what to fund.

* Scores each candidate on value (NPV from tool 2), strategic fit, feasibility and delivery-capacity fit.
* Funds committed/must-do projects first, then the rest by priority — value per pound of capital, tilted by the strategic score — until the CapEx budget or the delivery slots run out.
* Shows what it deferred and why (negative NPV, no slot, or would breach budget). Nothing is dropped silently.

In the worked FY27 portfolio it funds 6 of 9 stores for £8.7M of a £9.0M budget, capturing £11.1M of NPV, and defers £1.7M of requests with a reason on each.

```
python 01_investment_prioritiser/prioritiser.py 01_investment_prioritiser/portfolios/fy27.json
python 01_investment_prioritiser/prioritiser.py 01_investment_prioritiser/portfolios/fy27.json --budget 4000000 --max-slots 4
```

## 2. Store development economics

A transparent CapEx/OpEx model. For each store format it turns fit-out capital, rent, staffing, sales and a ramp into NPV, IRR, payback and return on invested capital, and gives an invest / review / reject verdict against a hurdle.

* Standard corporate-finance maths (NPV, IRR by bisection, interpolated payback), each output tracing back to an input in `formats.json`.
* A scenario toggle on the assumptions that matter most: slow the sales ramp or raise rent and watch the whole portfolio move. The compact format flips verdict first, which is exactly the assumption to defend.

```
python 02_store_economics/economics.py
python 02_store_economics/economics.py --format flagship --sales-ramp 0.85 --rent 1.1
```

## 3. Quarterly portfolio review pack

A quarterly review that writes its own first draft and cannot be circulated until a named person approves it.

* Bridges actual store openings and CapEx against plan by region, and splits the CapEx variance into a volume effect (fewer openings) and a cost-per-store effect — the two always tie to the total.
* Drafts the "what changed" commentary, labelling each explanation as a hypothesis. In the sample data it finds the planted story: the CapEx underspend is mostly phasing (slower openings), not saving, while one region ran hot on cost per store.
* Stays marked DRAFT until a reviewer approves. Approval is logged against a hash of the content, so if the numbers change the old sign-off no longer applies.

```
python 03_review_pack/generate_data.py
python 03_review_pack/review_pack.py
python 03_review_pack/review_pack.py --approve "Reviewer Name"
```

## Claude step (optional)

Everything runs without an API key. Set `ANTHROPIC_API_KEY` and `CLAUDE_MODEL`, install the `anthropic` package, and Claude rewrites the drafted wording. It is instructed to keep every number and label exactly as computed.

## Tests

```
pip install -r requirements.txt
python -m unittest tests.test_portfolio -v
```

The tests check NPV, IRR and payback against hand calculations, confirm the prioritiser respects the budget and delivery slots and never funds a negative-NPV store, confirm the CapEx bridge ties to the total variance, and confirm the review pack finds the planted cause and stays in draft until a content-bound approval is recorded.

## Showcase

```
python showcase/build_showcase.py
```

Builds `outputs/showcase.html` (and `outputs/index.html`): all three tools as one executive narrative, with every figure computed by the tools at build time. Design choices follow an answer-first, numbers-with-context house style.
