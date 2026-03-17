# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionReportWizard(models.TransientModel):
    _name = 'commission.report.wizard'
    _description = 'Commission Report Wizard'

    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        help="Start date for the report"
    )

    date_to = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
        help="End date for the report"
    )

    user_ids = fields.Many2many(
        'res.users',
        string='Salespersons',
        help="Select specific salespersons for the report. Leave empty for all."
    )

    report_type = fields.Selection([
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('comparison', 'Comparison Report'),
    ], string='Report Type', required=True, default='summary',
        help="Type of commission report to generate")

    group_by = fields.Selection([
        ('user', 'By Salesperson'),
        ('period', 'By Period'),
        ('product', 'By Product'),
        ('partner', 'By Customer'),
    ], string='Group By', default='user',
        help="How to group the report data")

    def action_generate_report(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))

        domain = [
            ('calculation_date', '>=', self.date_from),
            ('calculation_date', '<=', self.date_to),
            ('state', 'in', ['calculated', 'invoiced', 'paid']),
        ]

        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))

        commission_records = self.env['commission.record'].search(domain)

        if not commission_records:
            raise UserError(_("No commission records found for the selected criteria."))

        data = {
            'ids': commission_records.ids,
            'model': 'commission.record',
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'user_ids': self.user_ids.ids,
                'report_type': self.report_type,
                'group_by': self.group_by,
            }
        }

        print("FINAL DATA SENT TO REPORT ---> ", data)
        ctx = {'report_data': data}
        if self.report_type == 'summary':
            return self.env.ref('advanced_sales_commission.action_report_commission_summary').with_context(
                report_data=data
            ).report_action(commission_records)

        elif self.report_type == 'detailed':
            return self.env.ref('advanced_sales_commission.action_report_commission_detailed').with_context(
                report_data=data
            ).report_action(commission_records)

        elif self.report_type == 'comparison':
            return self.env.ref('advanced_sales_commission.action_report_commission_comparison').with_context(
                report_data=data
            ).report_action(commission_records)
        else:
            raise UserError(_("Invalid report type selected."))

class CommissionComparisonReport(models.AbstractModel):
    _name = 'report.advanced_sales_commission.report_commission_comparison'
    _description = "Commission Comparison Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env['commission.record'].browse(docids)

        # Group data USER-WISE
        user_groups = {}
        for rec in docs:
            user = rec.user_id
            if user.id not in user_groups:
                user_groups[user.id] = {
                    'user': user,
                    'total_sales': 0.0,
                    'total_commission': 0.0,
                    'orders': 0,
                }
            user_groups[user.id]['total_sales'] += rec.base_amount
            user_groups[user.id]['total_commission'] += rec.commission_amount
            user_groups[user.id]['orders'] += 1

        # Convert dict → list for QWeb
        comparison_lines = list(user_groups.values())

        return {
            'docs': docs,
            'form': data.get('form'),
            'comparison_lines': comparison_lines,
        }

