{
    'name': 'Analytic Distribution Wizard',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Bulk assign or remove analytic accounts on purchase order and invoice lines via wizard',
    'author': 'Detalex GmbH',
    'website': 'https://detalex.de',
    'support': 'support@detalex.de',
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
}
