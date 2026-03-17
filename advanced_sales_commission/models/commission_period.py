# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class CommissionPeriod(models.Model):
    _name = 'commission.period'
    _description = 'Commission Period'
    _order = 'date_from desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Period Name',
        required=True,
        help="Name of the commission period"
    )
    
    code = fields.Char(
        string='Period Code',
        help="Short code for the period"
    )
    
    date_from = fields.Date(
        string='Start Date',
        required=True,
        help="Start date of the commission period"
    )
    
    date_to = fields.Date(
        string='End Date',
        required=True,
        help="End date of the commission period"
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], string='State', default='draft', required=True,
       help="State of the commission period")
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company for which this period applies"
    )
    
    # Period type for automatic generation
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ], string='Period Type', default='monthly',
       help="Type of period for automatic generation")
    
    # Commission records
    commission_ids = fields.One2many(
        'commission.record',
        'period_id',
        string='Commission Records',
        help="Commission records for this period"
    )
    
    # Computed fields
    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_stats',
        store=True
    )
    
    total_commission = fields.Float(
        string='Total Commission',
        compute='_compute_commission_stats',
        digits=(12, 2),
        store=True
    )
    
    total_sales = fields.Float(
        string='Total Sales',
        compute='_compute_commission_stats',
        digits=(12, 2),
        store=True
    )
    
    avg_commission_rate = fields.Float(
        string='Average Commission Rate (%)',
        compute='_compute_commission_stats',
        digits=(12, 4),
        store=True
    )
    
    user_count = fields.Integer(
        string='Salesperson Count',
        compute='_compute_commission_stats',
        store=True
    )
    
    @api.depends('commission_ids.commission_amount', 'commission_ids.base_amount')
    def _compute_commission_stats(self):
        for period in self:
            commissions = period.commission_ids.filtered(lambda r: r.state in ['calculated', 'invoiced', 'paid'])
            
            period.commission_count = len(commissions)
            period.total_commission = sum(commissions.mapped('commission_amount'))
            period.total_sales = sum(commissions.mapped('base_amount'))
            period.user_count = len(commissions.mapped('user_id'))
            
            if period.total_sales:
                period.avg_commission_rate = (period.total_commission / period.total_sales) * 100
            else:
                period.avg_commission_rate = 0.0
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for period in self:
            if period.date_from >= period.date_to:
                raise ValidationError(_("Start date must be before end date."))
    
    @api.constrains('date_from', 'date_to', 'company_id')
    def _check_overlapping_periods(self):
        """Ensure no overlapping periods for the same company"""
        for period in self:
            domain = [
                ('company_id', '=', period.company_id.id),
                ('id', '!=', period.id),
                '|',
                '&', ('date_from', '<=', period.date_from), ('date_to', '>=', period.date_from),
                '&', ('date_from', '<=', period.date_to), ('date_to', '>=', period.date_to),
            ]
            
            overlapping = self.search(domain)
            if overlapping:
                raise ValidationError(_(
                    "Period dates overlap with existing period: %s"
                ) % overlapping[0].name)
    
    def action_open(self):
        """Open the commission period"""
        for period in self:
            if period.state != 'draft':
                raise UserError(_("Only draft periods can be opened."))
            period.state = 'open'
    
    def action_close(self):
        """Close the commission period"""
        for period in self:
            if period.state != 'open':
                raise UserError(_("Only open periods can be closed."))
            
            # Ensure all commissions are calculated
            draft_commissions = period.commission_ids.filtered(lambda r: r.state == 'draft')
            if draft_commissions:
                draft_commissions.action_calculate()
            
            period.state = 'closed'
    
    def action_reopen(self):
        """Reopen a closed period"""
        for period in self:
            if period.state != 'closed':
                raise UserError(_("Only closed periods can be reopened."))
            period.state = 'open'
    
    def action_calculate_commissions(self):
        """Calculate all commissions for this period"""
        self.ensure_one()
        
        if self.state == 'closed':
            raise UserError(_("Cannot calculate commissions for closed periods."))
        
        # Find all sale orders in this period that haven't been processed
        orders = self.env['sale.order'].search([
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
            ('state', 'in', ['sale', 'done']),
            ('commission_calculated', '=', False),
        ])
        
        commission_records = self.env['commission.record']
        
        for order in orders:
            records = self.env['commission.record'].calculate_commissions_for_order(order)
            if records:
                commission_records |= records
                # Update commission records with period
                records.write({'period_id': self.id})
                order.commission_calculated = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Commission Calculation'),
                'message': _('%d commission records created for %d orders.') % (
                    len(commission_records), len(orders)
                ),
                'type': 'success',
            }
        }
    
    def action_view_commissions(self):
        """View commission records for this period"""
        self.ensure_one()
        return {
            'name': _('Commission Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.record',
            'view_mode': 'list,form',
            'domain': [('period_id', '=', self.id)],
            'context': {'default_period_id': self.id},
        }

    def calculate_commissions_for_order(self, order):
        created = []
        for line in order.order_line:
            config = self.env['commission.config'].search([('product_id', '=', line.product_id.id)], limit=1)
            if config:
                record = self.create_commission_record(line, config)
                created.append(record.id)
        _logger.info("Commission Records Created: %s", created)
        return created
    @api.model
    def cron_create_next_period(self):
        """Create commission period for next month if not exists"""

        today = datetime.now().date()
        next_month = today.replace(day=1) + relativedelta(months=1)
        period_end = next_month + relativedelta(months=1) - timedelta(days=1)

        existing_period = self.search([
            ('date_from', '=', next_month),
            ('date_to', '=', period_end),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if not existing_period:
            self.create_period(
                next_month,
                period_end,
                'monthly',
                self.env.company.id
            )
    def action_generate_invoices(self):
        """Generate commission invoices for this period"""
        self.ensure_one()
        
        # Get calculated commissions that haven't been invoiced
        commissions = self.commission_ids.filtered(
            lambda r: r.state == 'calculated' and not r.invoice_commission_id
        )
        
        if not commissions:
            raise UserError(_("No calculated commissions found to invoice."))
        
        # Group by salesperson
        grouped_commissions = {}
        for commission in commissions:
            user_id = commission.user_id.id
            if user_id not in grouped_commissions:
                grouped_commissions[user_id] = []
            grouped_commissions[user_id].append(commission)
        
        invoices_created = 0
        
        for user_id, user_commissions in grouped_commissions.items():
            user = self.env['res.users'].browse(user_id)
            
            # Create invoice
            invoice_lines = []
            for commission in user_commissions:
                invoice_lines.append((0, 0, {
                    'name': commission.name,
                    'quantity': 1,
                    'price_unit': commission.commission_amount,
                    'account_id': commission._get_commission_account().id,
                }))
            
            invoice_vals = {
                'move_type': 'in_invoice',
                'partner_id': user.partner_id.id,
                'invoice_date': fields.Date.today(),
                'ref': f"Commission Period: {self.name}",
                'invoice_line_ids': invoice_lines,
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            
            # Update commission records
            for commission in user_commissions:
                commission.write({
                    'invoice_commission_id': invoice.id,
                    'state': 'invoiced',
                })
            
            invoices_created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoice Generation'),
                'message': _('%d commission invoices created.') % invoices_created,
                'type': 'success',
            }
        }
    
    @api.model
    def create_period(self, date_from, date_to, period_type='custom', company_id=None):
        """Create a new commission period"""
        if not company_id:
            company_id = self.env.company.id
        
        # Generate period name based on dates
        if period_type == 'monthly':
            name = date_from.strftime('%B %Y')
            code = date_from.strftime('%Y-%m')
        elif period_type == 'quarterly':
            quarter = (date_from.month - 1) // 3 + 1
            name = f"Q{quarter} {date_from.year}"
            code = f"{date_from.year}-Q{quarter}"
        elif period_type == 'yearly':
            name = str(date_from.year)
            code = str(date_from.year)
        else:
            name = f"{date_from.strftime('%b %Y')} - {date_to.strftime('%b %Y')}"
            code = f"{date_from.strftime('%Y%m')}-{date_to.strftime('%Y%m')}"
        
        return self.create({
            'name': name,
            'code': code,
            'date_from': date_from,
            'date_to': date_to,
            'period_type': period_type,
            'company_id': company_id,
        })
    
    @api.model
    def generate_periods(self, start_date, end_date, period_type='monthly', company_id=None):
        """Generate multiple periods between start and end dates"""
        if not company_id:
            company_id = self.env.company.id
        
        periods = self.env['commission.period']
        current_date = start_date
        
        while current_date <= end_date:
            if period_type == 'monthly':
                period_end = current_date + relativedelta(months=1) - relativedelta(days=1)
            elif period_type == 'quarterly':
                period_end = current_date + relativedelta(months=3) - relativedelta(days=1)
            elif period_type == 'yearly':
                period_end = current_date + relativedelta(years=1) - relativedelta(days=1)
            else:
                break
            
            if period_end > end_date:
                period_end = end_date
            
            period = self.create_period(current_date, period_end, period_type, company_id)
            periods |= period
            
            if period_type == 'monthly':
                current_date = current_date + relativedelta(months=1)
            elif period_type == 'quarterly':
                current_date = current_date + relativedelta(months=3)
            elif period_type == 'yearly':
                current_date = current_date + relativedelta(years=1)
            else:
                break
        
        return periods

