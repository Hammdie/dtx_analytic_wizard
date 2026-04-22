{
    'name': 'Analytic Distribution Wizard',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Bulk assign or remove analytic accounts on purchase order and invoice lines via wizard',
    'description': """
Analytic Distribution Wizard
=============================

Bulk manage analytic distribution on purchase orders and vendor bills.

Features:
- Assign analytic accounts to all lines of selected purchase orders or invoices at once
- Remove specific or all analytic accounts from selected document lines
- Merge new analytic accounts with existing distributions
- Available as server action from both list and form views
- Only allows changes on draft documents — confirmed purchase orders and posted invoices are protected
""",
    'author': 'Detalex GmbH',
    'website': 'https://detalex.de',
    'depends': [
        'purchase',
        'account',
        'analytic',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/analytic_distribution_wizard_views.xml',
        'data/server_actions.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'OPL-1',
    'price': 51.00,
    'currency': 'EUR',
    'assets': {
        'web.assets_tests': [
            'dtx_analytic_wizard/static/tests/tours/analytic_wizard_tour.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
