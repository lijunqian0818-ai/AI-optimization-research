"""Backtest core: rule calendar, synthetic fills, lot ledger, labels, attribution, event
table, delisting dispositions, universe and candidate filters, monitoring counts.

Stage-3 engine library (conventions of experiments/PLAN.md v0.7).  Tested on synthetic data
and on the raw files that have landed; it contains no model, no signal and produces no
strategy performance number by itself.

  config.py         parameters, their status, the conventions hash
  rule_calendar.py  dated rules (trading mechanics, limits, costs, taxes, disclosure regimes)
  market.py         bars, events, valuation rules OV / CV
  fills.py          SF / SF-strict / SF-loose, capacity cap
  costs.py          costs of one executed order
  ledger.py         share-and-cash ledger by entry lot
  labels.py         O1 decision tree; deadline (bracket) labels
  attribution.py    return track, Lemma 3 on two intervals, reference cost
  simulate.py       day loop from nominations to orders, fills and bookings; result records
  event_table.py    merge of the event sources EV1-EV3 with the backstop EV4 (PLAN 3.11)
  dispositions.py   delisting disposition table (PLAN 3.11 rule 11)
  universe.py       universe U-LIQ and the candidate set
  monitor.py        monitoring counts K_T, P_T; R2 / R3 report
  io_baostock.py    read-only loader of the raw files
  synth.py          random synthetic markets for the tests
"""
