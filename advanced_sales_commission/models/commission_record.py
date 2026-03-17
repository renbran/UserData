# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class CommissionRecord(models.Model):
    _name = 'commission.record'
    _description = 'Commission Record'
    _order = 'calculation_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Description',
        required=True,
        help="Description of the commission record"
    )

    # Basic information
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
        index=True,
        help="Salesperson who earned this commission"
    )

    manager_id = fields.Many2one(
        'res.users',
        string='Sales Manager',
        help="Sales manager who gets a commission from this sale"
    )

    director_id = fields.Many2one(
        'res.users',
        string='Sales Director',
        help="Sales director who gets a commission from this sale"
    )

    # Source documents
    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="Source sale order"
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help="Source invoice"
    )

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Order Line',
        help="Source order line"
    )

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        help="Source invoice line"
    )

    # Product and partner information
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Product for which commission is calculated"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help="Customer for which commission is calculated"
    )

    # Commission configuration
    commission_config_id = fields.Many2one(
        'commission.config',
        string='Commission Configuration',
        required=True,
        help="Commission configuration used for calculation"
    )

    commission_rule_id = fields.Many2one(
        'commission.rule',
        string='Commission Rule',
        help="Specific rule used for calculation"
    )

    # Amounts and calculations
    base_amount = fields.Float(
        string='Base Amount',
        digits=(12, 2),
        required=True,
        help="Amount on which commission is calculated"
    )

    commission_amount = fields.Float(
        string="Commission Amount",
        compute="_compute_commission_amount",
        store=True,
        readonly=False
    )

    @api.depends('base_amount', 'commission_rate')
    def _compute_commission_amount(self):
        for record in self:
            if record.base_amount and record.commission_rate:
                record.commission_amount = record.base_amount * record.commission_rate / 100
            else:
                record.commission_amount = 0.0

    manager_commission = fields.Float(
        string='Manager Commission',
        digits=(12, 2),
        help="Commission amount for the sales manager"
    )

    director_commission = fields.Float(
        string='Director Commission',
        digits=(12, 2),
        help="Commission amount for the sales director"
    )

    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(12, 4),
        help="Applied commission rate"
    )

    # Dates and periods
    calculation_date = fields.Datetime(
        string='Calculation Date',
        required=True,
        default=fields.Datetime.now,
        help="Date when commission was calculated"
    )

    sale_date = fields.Date(
        string='Sale Date',
        help="Date of the sale"
    )

    invoice_date = fields.Date(
        string='Invoice Date',
        help="Date of the invoice"
    )

    period_id = fields.Many2one(
        'commission.period',
        string='Commission Period',
        help="Commission period this record belongs to"
    )

    # State and processing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True,
        help="State of the commission record")

    # Invoice generation
    invoice_commission_id = fields.Many2one(
        'account.move',
        string='Commission Invoice',
        help="Invoice generated for this commission"
    )

    invoice_line_commission_id = fields.Many2one(
        'account.move.line',
        string='Commission Invoice Line',
        help="Invoice line for this commission"
    )

    # Additional information
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help="Currency of the commission amounts"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company for which this commission is calculated"
    )

    notes = fields.Text(
        string='Notes',
        help="Additional notes for this commission record"
    )

    # Computed fields
    total_commission = fields.Float(
        string='Total Commission',
        compute='_compute_total_commission',
        digits=(12, 2),
        store=True,
        help="Total commission including manager and director commissions"
    )

    is_invoiced = fields.Boolean(
        string='Is Invoiced',
        compute='_compute_is_invoiced',
        store=True,
        help="Whether this commission has been invoiced"
    )

    @api.model
    def cron_calculate_commissions(self):
        """Cron job to calculate commissions for last 7 days"""
        from datetime import datetime, timedelta

        date_from = datetime.now() - timedelta(days=7)
        orders = self.env['sale.order'].search([
            ('date_order', '>=', date_from),
            ('state', 'in', ['sale', 'done']),
            ('commission_calculated', '=', False),
        ])

        for order in orders:
            try:
                self.calculate_commissions_for_order(order)
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Commission Calculation Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': f"Error calculating commission for order {order.name}: {str(e)}",
                    'path': 'advanced_sales_commission',
                    'func': 'cron_calculate_commissions',
                })

    @api.model
    def cron_update_invoice_status(self):
        """Update commission status if related invoice is paid"""
        invoiced_commissions = self.search([
            ('state', '=', 'invoiced'),
            ('invoice_commission_id', '!=', False),
        ])

        for commission in invoiced_commissions:
            if commission.invoice_commission_id.payment_state == 'paid':
                commission.state = 'paid'

    @api.depends('commission_amount', 'manager_commission', 'director_commission')
    def _compute_total_commission(self):
        for record in self:
            record.total_commission = (
                    record.commission_amount +
                    record.manager_commission +
                    record.director_commission
            )

    @api.depends('invoice_commission_id')
    def _compute_is_invoiced(self):
        for record in self:
            record.is_invoiced = bool(record.invoice_commission_id)

    @api.constrains('commission_amount', 'manager_commission', 'director_commission')
    def _check_commission_amounts(self):
        for record in self:
            if record.commission_amount < 0:
                raise ValidationError(_("Commission amount cannot be negative."))
            if record.manager_commission < 0:
                raise ValidationError(_("Manager commission cannot be negative."))
            if record.director_commission < 0:
                raise ValidationError(_("Director commission cannot be negative."))

    @api.constrains('base_amount')
    def _check_base_amount(self):
        for record in self:
            if record.base_amount == 0:
                raise ValidationError(_("Base amount cannot be zero."))

    def action_calculate(self):
        """Calculate commission for this record"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Can only calculate commission for draft records."))

            # Get the commission configuration and calculate
            if record.order_line_id:
                commission_amount = record.commission_config_id.calculate_commission(
                    record.order_line_id, record.base_amount
                )
                record.commission_amount = commission_amount

            # Calculate hierarchical commissions
            assignment = self.env['commission.assignment'].get_assignment_for_user(
                record.user_id.id, record.sale_date or fields.Date.today()
            )

            if assignment:
                if assignment.manager_id and assignment.manager_rate:
                    record.manager_id = assignment.manager_id
                    record.manager_commission = record.base_amount * (assignment.manager_rate / 100)

                if assignment.director_id and assignment.director_rate:
                    record.director_id = assignment.director_id
                    record.director_commission = record.base_amount * (assignment.director_rate / 100)

            record.state = 'calculated'

    def action_invoice(self):
        """Generate invoice for this commission"""
        for record in self:
            if record.state != 'calculated':
                raise UserError(_("Can only invoice calculated commission records."))

            if record.invoice_commission_id:
                raise UserError(_("Commission already invoiced."))

            commission_account = self._get_commission_account()

            # Create vendor bill for commission
            invoice_vals = {
                'move_type': 'in_invoice',
                'partner_id': record.user_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'ref': f"Commission: {record.name}",
                'invoice_line_ids': [(0, 0, {
                    'name': record.name,
                    'quantity': 1,
                    'price_unit': record.commission_amount,
                    'account_id': commission_account.id,
                })],
            }

            invoice = self.env['account.move'].create(invoice_vals)

            # link invoice line properly
            invoice_line = invoice.invoice_line_ids[0] if invoice.invoice_line_ids else False

            # update commission record with missing required fields
            record.write({
                'invoice_commission_id': invoice.id,
                'invoice_id': invoice.id,
                'invoice_line_id': invoice_line.id if invoice_line else False,
                'invoice_date': invoice.invoice_date,
                'commission_rule_id': record.commission_config_id.id if record.commission_config_id else False,
                'invoice_line_commission_id': invoice_line.id if invoice_line else False,
                'period_id': self.env['commission.period'].get_current_period().id if hasattr(
                    self.env['commission.period'], 'get_current_period') else False,
                'state': 'invoiced',
            })

    def action_cancel(self):
        """Cancel this commission record"""
        for record in self:
            if record.state == 'paid':
                raise UserError(_("Cannot cancel paid commission records."))

            if record.invoice_commission_id and record.invoice_commission_id.state == 'posted':
                raise UserError(_("Cannot cancel commission with posted invoice."))

            record.state = 'cancelled'

    def action_reset_to_draft(self):
        """Reset commission record to draft"""
        for record in self:
            if record.invoice_commission_id:
                raise UserError(_("Cannot reset invoiced commission to draft."))

            record.state = 'draft'

    def _get_commission_account(self):
        """Get the account for commission expenses"""
        account = self.env['account.account'].search([
            ('code', '=', '6222000'),  # Commission expense account

        ], limit=1)

        if not account:
            # Fallback to any expense account
            account = self.env['account.account'].search([
                ('account_type', '=', 'expense'),
            ], limit=1)

        if not account:
            raise UserError(_("No commission expense account found. Please configure account 622000."))

        return account

    @api.model
    def create_commission_record(self, order_line, config, assignment=None):
        """Create a commission record for an order line"""
        if not assignment:
            assignment = self.env['commission.assignment'].get_assignment_for_user(
                order_line.order_id.user_id.id,
                order_line.order_id.date_order.date()
            )

        if not assignment:
            _logger.warning(f"No commission assignment found for user {order_line.order_id.user_id.name}")
            return False

        # Calculate base amount
        base_amount = order_line.price_subtotal

        # Create commission record
        vals = {
            'name': f"Commission for {order_line.product_id.name} - {order_line.order_id.name}",
            'user_id': order_line.order_id.user_id.id,
            'order_id': order_line.order_id.id,
            'order_line_id': order_line.id,
            'product_id': order_line.product_id.id,
            'partner_id': order_line.order_id.partner_id.id,
            'commission_config_id': config.id,
            'base_amount': base_amount,
            'sale_date': order_line.order_id.date_order.date(),
            'company_id': order_line.company_id.id,
        }

        record = self.create(vals)
        record.action_calculate()

        return record

    @api.model
    def calculate_commissions_for_order(self, order):
        """Calculate commissions for all lines in a sale order"""
        if order.commission_ids and any(rec.state != 'draft' for rec in order.commission_ids):
            return False

        if not order.user_id:
            return False

        config = self.env['commission.config'].get_applicable_config(
            order.user_id.id, order.date_order.date()
        )

        if not config or not config.auto_calculate:
            return False

        commission_records = self.env['commission.record']

        for line in order.order_line:
            if line.product_id.type == 'service' and not line.product_id.invoice_policy == 'order':
                continue

            record = self.create_commission_record(line, config)
            if record:
                commission_records |= record

        return commission_records
