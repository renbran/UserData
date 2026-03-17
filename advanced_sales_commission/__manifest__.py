# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
{
    'name': 'Advanced Sales Commission',
    'version': '17.0.0.0',
    'category': 'Sales',
    "author": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com",
    "company": "TechUltra Solutions Private Limited",
    'summary': """
    Advanced sales commission management with flexible rules and comprehensive reporting
    Odoo sales commission
    Advanced sales commission
    Odoo commission module
    Commission automation
    Sales commission tracking
    Odoo commission management
    Rule-based commission
    Multi-level commission structure
    Commission calculation
    Commission assignment
    Commission reporting
    Sales performance tracking
    Commission payout management
    Invoice-linked commissions
    Commission settlement
    Period-wise commission
    Odoo sales automation
    Sales incentive management
    Commission workflow
    Sales commission configuration
    Sales team commission
    Odoo ERP commission
    Automated commission system
    Commission rules setup
    Product-wise commission
    Salesperson commission tracking
    Commission rate configuration
    Odoo business automation
    Performance-based incentives
    Commission management software
    odoo19
    odoo18
    odoo17
    tus
    TUS
    Techultra solutions
    Techultra solutions private solutions
    techultra solutions private limited
    """,
    'description': """
    The Advanced Sales Commission module automates and streamlines the calculation, assignment, tracking, and reporting of sales commissions in Odoo. It supports rule-based commissions, multi-level structures, period-wise settlements, and invoice-linked payouts, giving businesses a powerful and flexible commission management system.
    Odoo sales commission
    Advanced sales commission
    Odoo commission module
    Commission automation
    Sales commission tracking
    Odoo commission management
    Rule-based commission
    Multi-level commission structure
    Commission calculation
    Commission assignment
    Commission reporting
    Sales performance tracking
    Commission payout management
    Invoice-linked commissions
    Commission settlement
    Period-wise commission
    Odoo sales automation
    Sales incentive management
    Commission workflow
    Sales commission configuration
    Sales team commission
    Odoo ERP commission
    Automated commission system
    Commission rules setup
    Product-wise commission
    Salesperson commission tracking
    Commission rate configuration
    Odoo business automation
    Performance-based incentives
    Commission management software
    odoo19
    odoo18
    odoo17
    tus
    TUS
    Techultra solutions
    Techultra solutions private solutions
    techultra solutions private limited
    """,
    'license': 'OPL-1',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'account',
        'sale_margin',
    ],
    'data': [
        # Security
        'security/commission_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/commission_data.xml',
        'data/commission_cron.xml',

        # Views
        'views/commission_config_views.xml',
        'views/commission_rule_views.xml',
        'views/commission_assignment_views.xml',
        'views/commission_record_views.xml',
        'views/commission_period_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',

        # Wizards
        'wizards/commission_calculate_wizard_views.xml',
        'wizards/commission_report_wizard_views.xml',
        'wizards/commission_invoice_wizard_views.xml',
        'views/commission_menus.xml',

        # Reports
        'report/commission_report_templates.xml',
        'report/commission_reports.xml',
    ],
    'demo': [
        'data/commission_demo.xml',
    ],
    "images": ["static/description/main_screen.gif"],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
}
