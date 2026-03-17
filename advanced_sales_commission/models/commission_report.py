# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class CommissionReport(models.Model):
    _name = 'commission.report'
    _description = 'Commission Report'
    _auto = False
    _rec_name = 'user_id'

    # Basic fields
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    category_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    commission_config_id = fields.Many2one('commission.config', string='Commission Configuration', readonly=True)
    period_id = fields.Many2one('commission.period', string='Commission Period', readonly=True)

    # Date fields
    date = fields.Date(string='Date', readonly=True)
    year = fields.Char(string='Year', readonly=True)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', readonly=True)
    quarter = fields.Char(string='Quarter', readonly=True)

    # Amount fields
    total_sales = fields.Float(string='Total Sales', readonly=True, digits=(12, 2))
    total_commission = fields.Float(string='Total Commission', readonly=True, digits=(12, 2))
    manager_commission = fields.Float(string='Manager Commission', readonly=True, digits=(12, 2))
    director_commission = fields.Float(string='Director Commission', readonly=True, digits=(12, 2))

    # Count fields
    commission_count = fields.Integer(string='Commission Count', readonly=True)
    order_count = fields.Integer(string='Order Count', readonly=True)

    # Rate fields
    avg_commission_rate = fields.Float(string='Average Commission Rate (%)', readonly=True, digits=(12, 4))

    # State field
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
    ], string='State', readonly=True)

    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        """Create the view for commission reporting"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    cr.user_id,
                    cr.partner_id,
                    cr.product_id,
                    pt.categ_id AS category_id,
                    cr.commission_config_id,
                    cr.period_id,
                    cr.calculation_date::date AS date,
                    EXTRACT(year FROM cr.calculation_date) AS year,
                    TO_CHAR(cr.calculation_date, 'MM') AS month,
                    'Q' || EXTRACT(quarter FROM cr.calculation_date) AS quarter,
                    SUM(cr.base_amount) AS total_sales,
                    SUM(cr.commission_amount) AS total_commission,
                    SUM(cr.manager_commission) AS manager_commission,
                    SUM(cr.director_commission) AS director_commission,
                    COUNT(cr.id) AS commission_count,
                    COUNT(DISTINCT cr.order_id) AS order_count,
                    CASE 
                        WHEN SUM(cr.base_amount) > 0 
                        THEN (SUM(cr.commission_amount) / SUM(cr.base_amount)) * 100 
                        ELSE 0 
                    END AS avg_commission_rate,
                    cr.state,
                    cr.company_id
                FROM commission_record cr
                LEFT JOIN product_product pp ON cr.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE cr.state IN ('calculated', 'invoiced', 'paid')
                GROUP BY
                    cr.user_id,
                    cr.partner_id,
                    cr.product_id,
                    pt.categ_id,
                    cr.commission_config_id,
                    cr.period_id,
                    cr.calculation_date::date,
                    EXTRACT(year FROM cr.calculation_date),
                    TO_CHAR(cr.calculation_date, 'MM'),
                    EXTRACT(quarter FROM cr.calculation_date),
                    cr.state,
                    cr.company_id
            )
        """ % self._table)


class CommissionDateRangeReport(models.TransientModel):
    _name = 'commission.date.range.report'
    _description = 'Commission Date Range Report'

    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        help="Start date for the commission report"
    )

    date_to = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
        help="End date for the commission report"
    )

    user_ids = fields.Many2many(
        'res.users',
        string='Salespersons',
        help="Select specific salespersons for the report. Leave empty for all."
    )

    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        help="Select specific customers for the report. Leave empty for all."
    )

    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        help="Select specific products for the report. Leave empty for all."
    )

    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help="Select specific product categories for the report. Leave empty for all."
    )

    group_by = fields.Selection([
        ('user', 'By Salesperson'),
        ('partner', 'By Customer'),
        ('product', 'By Product'),
        ('category', 'By Product Category'),
        ('date', 'By Date'),
        ('month', 'By Month'),
        ('quarter', 'By Quarter'),
        ('year', 'By Year'),
    ], string='Group By', default='user', required=True,
        help="How to group the report data")

    include_draft = fields.Boolean(
        string='Include Draft',
        help="Include draft commission records in the report"
    )

    include_cancelled = fields.Boolean(
        string='Include Cancelled',
        help="Include cancelled commission records in the report"
    )

    def action_generate_report(self):
        """Generate the date range commission report"""
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))

        # Build domain for filtering
        domain = [
            ('calculation_date', '>=', self.date_from),
            ('calculation_date', '<=', self.date_to),
        ]

        # Add state filter
        states = ['calculated', 'invoiced', 'paid']
        if self.include_draft:
            states.append('draft')
        if self.include_cancelled:
            states.append('cancelled')
        domain.append(('state', 'in', states))

        # Add optional filters
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.category_ids:
            domain.append(('category_id', 'in', self.category_ids.ids))

        # Get commission records
        commission_records = self.env['commission.record'].search(domain)

        if not commission_records:
            raise UserError(_("No commission records found for the selected criteria."))

        # Generate report data
        report_data = self._generate_report_data(commission_records)

        # Return action to display the report
        return {
            'name': _('Commission Date Range Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.date.range.report.line',
            'view_mode': 'list',
            'target': 'new',
            'context': {
                'default_report_data': report_data,
                'group_by': self.group_by,
            },
        }

    def _generate_report_data(self, commission_records):
        """Generate aggregated report data"""
        data = {}

        for record in commission_records:
            # Determine grouping key
            if self.group_by == 'user':
                key = record.user_id.name
            elif self.group_by == 'partner':
                key = record.partner_id.name if record.partner_id else 'Unknown'
            elif self.group_by == 'product':
                key = record.product_id.name if record.product_id else 'Unknown'
            elif self.group_by == 'category':
                key = record.product_id.categ_id.name if record.product_id and record.product_id.categ_id else 'Unknown'
            elif self.group_by == 'date':
                key = record.calculation_date.strftime('%Y-%m-%d')
            elif self.group_by == 'month':
                key = record.calculation_date.strftime('%Y-%m')
            elif self.group_by == 'quarter':
                quarter = (record.calculation_date.month - 1) // 3 + 1
                key = f"{record.calculation_date.year}-Q{quarter}"
            elif self.group_by == 'year':
                key = str(record.calculation_date.year)
            else:
                key = 'All'

            # Aggregate data
            if key not in data:
                data[key] = {
                    'name': key,
                    'total_sales': 0.0,
                    'total_commission': 0.0,
                    'manager_commission': 0.0,
                    'director_commission': 0.0,
                    'commission_count': 0,
                    'avg_commission_rate': 0.0,
                }

            data[key]['total_sales'] += record.base_amount
            data[key]['total_commission'] += record.commission_amount
            data[key]['manager_commission'] += record.manager_commission
            data[key]['director_commission'] += record.director_commission
            data[key]['commission_count'] += 1

        # Calculate average commission rates
        for key, values in data.items():
            if values['total_sales'] > 0:
                values['avg_commission_rate'] = (values['total_commission'] / values['total_sales']) * 100

        return list(data.values())


class CommissionDateRangeReportLine(models.TransientModel):
    _name = 'commission.date.range.report.line'
    _description = 'Commission Date Range Report Line'

    name = fields.Char(string='Group', readonly=True)
    total_sales = fields.Float(string='Total Sales', readonly=True, digits=(12, 2))
    total_commission = fields.Float(string='Total Commission', readonly=True, digits=(12, 2))
    manager_commission = fields.Float(string='Manager Commission', readonly=True, digits=(12, 2))
    director_commission = fields.Float(string='Director Commission', readonly=True, digits=(12, 2))
    commission_count = fields.Integer(string='Commission Count', readonly=True)
    avg_commission_rate = fields.Float(string='Average Commission Rate (%)', readonly=True, digits=(12, 4))