{
    'name': 'Analytic Distribution Wizard',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Assign analytic accounts to all order/invoice lines via wizard',
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
    'installable': True,
    'auto_install': False,
}
