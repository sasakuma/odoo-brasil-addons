# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.total_tax = sum(l.price_tax for l in lines)
        self.icms_base = sum(l.icms_base_calculo for l in lines)
        self.icms_value = sum(l.icms_valor for l in lines)
        self.icms_st_base = sum(l.icms_st_base_calculo for l in lines)
        self.icms_st_value = sum(l.icms_st_valor for l in lines)
        self.valor_icms_uf_remet = sum(l.icms_uf_remet for l in lines)
        self.valor_icms_uf_dest = sum(l.icms_uf_dest for l in lines)
        self.valor_icms_fcp_uf_dest = sum(l.icms_fcp_uf_dest for l in lines)
        self.issqn_base = sum(l.issqn_base_calculo for l in lines)
        self.issqn_value = sum(abs(l.issqn_valor) for l in lines)
        self.ipi_base = sum(l.ipi_base_calculo for l in lines)
        self.ipi_value = sum(l.ipi_valor for l in lines)
        self.pis_base = sum(l.pis_base_calculo for l in lines)
        self.pis_value = sum(abs(l.pis_valor) for l in lines)
        self.cofins_base = sum(l.cofins_base_calculo for l in lines)
        self.cofins_value = sum(abs(l.cofins_valor) for l in lines)
        self.ii_value = sum(l.ii_valor for l in lines)
        self.csll_base = sum(l.csll_base_calculo for l in lines)
        self.csll_value = sum(abs(l.csll_valor) for l in lines)
        self.irrf_base = sum(l.irrf_base_calculo for l in lines)
        self.irrf_value = sum(abs(l.irrf_valor) for l in lines)
        self.inss_base = sum(l.inss_base_calculo for l in lines)
        self.inss_value = sum(abs(l.inss_valor) for l in lines)

        # Retenções
        self.issqn_retention = sum(
            abs(l.issqn_valor) if l.issqn_valor < 0 else 0.0 for l in lines)
        self.pis_retention = sum(
            abs(l.pis_valor) if l.pis_valor < 0 else 0.0 for l in lines)
        self.cofins_retention = sum(
            abs(l.cofins_valor) if l.cofins_valor < 0 else 0.0 for l in lines)
        self.csll_retention = sum(
            abs(l.csll_valor) if l.csll_valor < 0 else 0 for l in lines)
        self.irrf_retention = sum(
            abs(l.irrf_valor) if l.irrf_valor < 0 else 0.0 for l in lines)
        self.inss_retention = sum(
            abs(l.inss_valor) if l.inss_valor < 0 else 0.0 for l in lines)

        self.total_bruto = sum(l.valor_bruto for l in lines)
        self.total_desconto = sum(l.valor_desconto for l in lines)
        self.total_tributos_federais = sum(
            l.tributos_estimados_federais for l in lines)
        self.total_tributos_estaduais = sum(
            l.tributos_estimados_estaduais for l in lines)
        self.total_tributos_municipais = sum(
            l.tributos_estimados_municipais for l in lines)
        self.total_tributos_estimados = sum(
            l.tributos_estimados for l in lines)
        # TOTAL
        self.amount_total = self.total_bruto - \
            self.total_desconto + self.total_tax
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = self.amount_total * sign
        self.amount_total_signed = self.amount_total * sign

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_receivables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "receivable":
                receivable_lines.append(line.id)
        self.receivable_move_line_ids = self.env['account.move.line'].browse(
            list(set(receivable_lines)))

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_payables(self):
        payable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "payable":
                payable_lines.append(line.id)
        self.payable_move_line_ids = self.env['account.move.line'].browse(
            list(set(payable_lines)))

    # @api.model
    # def _default_fiscal_document(self):
    #     company = self.env['res.company'].browse(self.env.user.company_id.id)
    #     return company.fiscal_document_for_product_id
    #
    # @api.model
    # def _default_fiscal_document_serie(self):
    #     company = self.env['res.company'].browse(self.env.user.company_id.id)
    #     return company.document_serie_id.id

    total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_compute_amount',
        digits=dp.get_precision('Account'), store=True)

    parcel_ids = fields.One2many(comodel_name='br_account.invoice.parcel',
                                 inverse_name='invoice_id',
                                 string='Parcelas')

    financial_operation_id = fields.Many2one('account.financial.operation',
                                             string=u'Operação Financeira')

    title_type_id = fields.Many2one('account.title.type',
                                    string=u'Tipo de Título')

    receivable_move_line_ids = fields.Many2many(
        'account.move.line', string='Receivable Move Lines',
        compute='_compute_receivables')

    payable_move_line_ids = fields.Many2many(
        'account.move.line', string='Payable Move Lines',
        compute='_compute_payables')

    issuer = fields.Selection(
        [('0', 'Terceiros'), ('1', u'Emissão própria')], 'Emitente',
        default='0', readonly=True, states={'draft': [('readonly', False)]})

    vendor_number = fields.Char(
        u'Número NF Entrada', size=18, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Número da Nota Fiscal do Fornecedor")

    vendor_serie = fields.Char(string=u'Série NF Entrada',
                               size=12,
                               readonly=True,
                               help=u"Série do número da Nota Fiscal do "
                                    u"Fornecedor")

    document_serie_id = fields.Many2one('br_account.document.serie',
                                        string=u'Série',
                                        readonly=True,
                                        states={
                                            'draft': [('readonly', False)],
                                        })

    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         string='Documento',
                                         readonly=True,
                                         states={
                                             'draft': [('readonly', False)],
                                         })

    is_eletronic = fields.Boolean(
        related='fiscal_document_id.electronic', type='boolean',
        store=True, string=u'Eletrônico', readonly=True)

    fiscal_document_related_ids = fields.One2many(
        'br_account.document.related', 'invoice_id',
        'Documento Fiscal Relacionado', readonly=True,
        states={'draft': [('readonly', False)]})

    fiscal_observation_ids = fields.Many2many(
        'br_account.fiscal.observation', string="Observações Fiscais",
        readonly=True, states={'draft': [('readonly', False)]})

    fiscal_comment = fields.Text(
        u'Observação Fiscal', readonly=True,
        states={'draft': [('readonly', False)]})

    total_bruto = fields.Float(
        string='Total Bruto ( = )', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    total_desconto = fields.Float(
        string='Desconto ( - )', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    icms_base = fields.Float(
        string='Base ICMS', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'))

    icms_value = fields.Float(
        string='Valor ICMS', digits=dp.get_precision('Account'),
        compute='_compute_amount', store=True)

    icms_st_base = fields.Float(
        string='Base ICMS ST', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'))

    icms_st_value = fields.Float(
        string='Valor ICMS ST', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'))

    valor_icms_fcp_uf_dest = fields.Float(
        string="Total ICMS FCP", store=True, compute='_compute_amount',
        help=u'Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino')

    valor_icms_uf_dest = fields.Float(
        string="ICMS Destino", store=True, compute='_compute_amount',
        help='Valor total do ICMS Interestadual para a UF de destino')

    valor_icms_uf_remet = fields.Float(
        string="ICMS Remetente", store=True, compute='_compute_amount',
        help='Valor total do ICMS Interestadual para a UF do Remetente')

    issqn_base = fields.Float(
        string='Base ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    issqn_value = fields.Float(
        string='Valor ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    issqn_retention = fields.Float(
        string='ISSQN Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    ipi_base = fields.Float(
        string='Base IPI', store=True, digits=dp.get_precision('Account'),
        compute='_compute_amount')

    ipi_base_other = fields.Float(
        string="Base IPI Outras", store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    ipi_value = fields.Float(
        string='Valor IPI', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    pis_base = fields.Float(
        string='Base PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    pis_value = fields.Float(
        string='Valor PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    pis_retention = fields.Float(
        string='PIS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    cofins_base = fields.Float(
        string='Base COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    cofins_value = fields.Float(
        string='Valor COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)

    cofins_retention = fields.Float(
        string='COFINS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)

    ii_value = fields.Float(
        string='Valor II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    csll_base = fields.Float(
        string='Base CSLL', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    csll_value = fields.Float(
        string='Valor CSLL', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    csll_retention = fields.Float(
        string='CSLL Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    irrf_base = fields.Float(
        string='Base IRRF', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    irrf_value = fields.Float(
        string='Valor IRRF', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    irrf_retention = fields.Float(
        string='IRRF Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    inss_base = fields.Float(
        string='Base INSS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    inss_value = fields.Float(
        string='Valor INSS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    inss_retention = fields.Float(
        string='INSS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    total_tributos_federais = fields.Float(
        string='Total de Tributos Federais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    total_tributos_estaduais = fields.Float(
        string='Total de Tributos Estaduais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    total_tributos_municipais = fields.Float(
        string='Total de Tributos Municipais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    total_tributos_estimados = fields.Float(
        string='Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    @api.onchange('issuer')
    def _onchange_issuer(self):
        if self.issuer == '0' and self.type in (u'in_invoice', u'in_refund'):
            self.fiscal_document_id = None
            self.document_serie_id = None

    @api.onchange('fiscal_document_id')
    def _onchange_fiscal_document_id(self):
        series = self.env['br_account.document.serie'].search(
            [('fiscal_document_id', '=', self.fiscal_document_id.id)])
        self.document_serie_id = series and series[0].id or False

    @api.onchange('fiscal_position_id')
    def _onchange_br_account_fiscal_position_id(self):
        if self.fiscal_position_id and self.fiscal_position_id.account_id:
            self.account_id = self.fiscal_position_id.account_id.id
        if self.fiscal_position_id and self.fiscal_position_id.journal_id:
            self.journal_id = self.fiscal_position_id.journal_id
        ob_ids = [x.id for x in self.fiscal_position_id.fiscal_observation_ids]
        self.fiscal_observation_ids = [(6, False, ob_ids)]

        self.fiscal_document_id = self.fiscal_position_id.fiscal_document_id.id

    def _create_move_line_from_payment_term(self, inv, ctx, total,
                                            total_currency, iml):
        """Sobrescreve criacao de move lines a partir das parcelas"""
        date_invoice = inv.date_invoice
        company_currency = inv.company_id.currency_id
        diff_currency = inv.currency_id != company_currency
        name = inv.name or '/'

        res_amount_currency = total_currency
        ctx['date'] = date_invoice

        for i, t in enumerate(self.parcel_ids):
            if inv.currency_id != company_currency:
                amount_currency = company_currency.with_context(ctx).compute(
                    t.parceling_value, inv.currency_id)
            else:
                amount_currency = False

            # last line: add the diff
            res_amount_currency -= amount_currency or 0
            if i + 1 == len(self.parcel_ids):
                amount_currency += res_amount_currency

            iml.append({
                'type': 'dest',
                'name': name,
                'price': t.parceling_value,
                'account_id': inv.account_id.id,
                'date_maturity': t.date_maturity,
                'amount_currency': diff_currency and amount_currency,
                'currency_id': diff_currency and inv.currency_id.id,
                'invoice_id': inv.id,
            })

        return iml

    @api.multi
    def action_create_periodic_entry(self):

        for inv in self:

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write(
                    {'date_invoice': fields.Date.context_today(self)})

            date_invoice = inv.date_invoice
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and
            # analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency

            total, total_currency, iml = inv.with_context(
                ctx).compute_invoice_totals(company_currency, iml)

            if inv.payment_term_id:
                lines = inv.with_context(ctx).payment_term_id.with_context(
                    currency_id=company_currency.id).compute(total, date_invoice)[0]

                res_amount_currency = total_currency
                ctx['date'] = date_invoice

                # Removemos as parcelas adicionadas anteriormente
                inv.parcel_ids.unlink()

                for i, t in enumerate(lines):
                    if inv.currency_id != company_currency:
                        amount_currency = \
                            company_currency.with_context(ctx).compute(
                                t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(lines):
                        amount_currency += res_amount_currency

                    teste = {
                        'name': str(i + 1).zfill(2),
                        'parceling_value': t[1],
                        'date_maturity': t[0],
                        'financial_operation_id': inv.financial_operation_id.id,
                        'title_type_id': inv.title_type_id.id,
                        'company_currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    }

                    self.env['br_account.invoice.parcel'].create(teste)

    @api.multi
    def action_invoice_cancel_paid(self):
        if self.filtered(lambda inv: inv.state not in ['proforma2', 'draft',
                                                       'open', 'paid']):
            raise UserError(_("Invoice must be in draft, Pro-forma or open \
                              state in order to be cancelled."))
        return self.action_cancel()

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        contador = 0

        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            res[contador]['price'] = line.price_total

            price = line.price_unit * (1 - (
                line.discount or 0.0) / 100.0)

            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)

            taxes_dict = tax_ids.compute_all(
                price, self.currency_id, line.quantity,
                product=line.product_id, partner=self.partner_id)

            for tax in line.invoice_line_tax_ids:
                tax_dict = next(
                    x for x in taxes_dict['taxes'] if x['id'] == tax.id)
                if not tax.price_include and tax.account_id:
                    res[contador]['price'] += tax_dict['amount']
                if tax.price_include and (not tax.account_id or
                                          not tax.deduced_account_id):
                    if tax_dict['amount'] > 0.0:  # Negativo é retido
                        res[contador]['price'] -= tax_dict['amount']

            contador += 1

        return res

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)
        count = 1
        for invoice_line in res:
            line = invoice_line[2]
            line['ref'] = self.origin
            if line['name'] == '/' or (
               line['name'] == self.name and self.name):
                line['name'] = "%02d" % count
                count += 1
        return res

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            other_taxes = line.invoice_line_tax_ids.filtered(
                lambda x: not x.domain)
            line.invoice_line_tax_ids = other_taxes | line.tax_icms_id | \
                line.tax_ipi_id | line.tax_pis_id | line.tax_cofins_id | \
                line.tax_issqn_id | line.tax_ii_id | line.tax_icms_st_id | \
                line.tax_simples_id | line.tax_csll_id | line.tax_irrf_id | \
                line.tax_inss_id

            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)

            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_ids.compute_all(
                price_unit, self.currency_id, line.quantity,
                line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(
                    tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()

        done_taxes = []
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount and tax_line.tax_id.deduced_account_id:
                tax = tax_line.tax_id
                done_taxes.append(tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount * -1,
                    'quantity': 1,
                    'price': tax_line.amount * -1,
                    'account_id': tax_line.tax_id.deduced_account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, done_taxes)]
                    if tax_line.tax_id.include_base_amount else []
                })
        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)

        res['fiscal_document_id'] = invoice.fiscal_document_id.id
        res['document_serie_id'] = invoice.document_serie_id.id
        return res
