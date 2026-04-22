============================
Analytic Distribution Wizard
============================

Bulk-manage analytic distributions on purchase orders and vendor bills
from a single server action, without editing each line by hand.

Features
========

* Assign one or more analytic accounts to every line of the selected
  purchase orders or invoices at once.
* Remove a specific analytic account — or every analytic account — from
  the selected document lines.
* Merge new analytic accounts with the existing distribution map, so
  pre-existing entries are preserved unless explicitly overwritten.
* Available as a server action from both the list and form views of
  ``purchase.order`` and ``account.move``.
* Draft-state guard: the wizard refuses to run on confirmed purchase
  orders and posted invoices so already-validated postings remain
  immutable.

Usage
=====

1. Select one or more purchase orders or vendor bills in the list
   view (or open a single document in the form view).
2. From the *Action* menu pick
   **Analytic Distribution Wizard → Assign** or **Remove**.
3. Fill in the analytic accounts and percentages and apply.

Dependencies
============

* ``purchase``
* ``account``
* ``analytic``

Bug Tracker
===========

Issues and feature requests: please contact
`support@detalex.de <mailto:support@detalex.de>`_.

Credits
=======

* Detalex GmbH <https://detalex.de>

License
=======

OPL-1 (Odoo Proprietary License v1.0).
