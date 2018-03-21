# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
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

        self.total_seguro = sum(l.valor_seguro for l in lines)
        self.total_frete = sum(l.valor_frete for l in lines)
        self.total_despesas = sum(l.outras_despesas for l in lines)
        self.amount_total = (self.total_bruto - self.total_desconto +
                             self.total_tax + self.total_frete +
                             self.total_seguro + self.total_despesas)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = self.amount_total * sign
        self.amount_total_signed = self.amount_total * sign

    total_seguro = fields.Float(
        string='Seguro ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount")
    total_despesas = fields.Float(
        string='Despesas ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount")
    total_frete = fields.Float(
        string='Frete ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount")

    # Transporte
    freight_responsibility = fields.Selection(
        [('0', '0 - Emitente'),
         ('1', '1 - Destinatário'),
         ('2', '2 - Terceiros'),
         ('9', '9 - Sem Frete')],
        'Modalidade do frete', default="9")
    carrier_id = fields.Many2one('res.partner', 'Transportadora')
    vehicle_plate = fields.Char('Placa do Veículo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_rntc = fields.Char('RNTC', size=20)

    tow_plate = fields.Char('Placa do Reboque', size=7)
    tow_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    tow_rntc = fields.Char('RNTC Reboque', size=20)

    weight = fields.Float(string='Peso Bruto', help="O peso bruto em Kg.")
    weight_net = fields.Float('Peso Líquido', help="O peso líquido em Kg.")
    number_of_packages = fields.Integer('Nº Volumes')
    kind_of_packages = fields.Char('Espécie', size=60)
    brand_of_packages = fields.Char('Marca', size=60)
    notation_of_packages = fields.Char('Numeração', size=60)

    # Exportação
    uf_saida_pais_id = fields.Many2one(
        'res.country.state', domain=[('country_id.code', '=', 'BR')],
        string="UF Saída do País")
    local_embarque = fields.Char('Local de Embarque', size=60)
    local_despacho = fields.Char('Local de Despacho', size=60)

    def _prepare_edoc_vals(self, inv):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv)
        res['valor_frete'] = inv.total_frete
        res['valor_despesas'] = inv.total_despesas
        res['valor_seguro'] = inv.total_seguro

        res['modalidade_frete'] = inv.freight_responsibility
        res['transportadora_id'] = inv.carrier_id.id
        res['placa_veiculo'] = (inv.vehicle_plate or '').upper()
        res['uf_veiculo'] = inv.vehicle_state_id.code
        res['rntc'] = inv.vehicle_rntc

        res['reboque_ids'] = [(0, None, {
            'uf_veiculo': inv.tow_state_id.code,
            'rntc': inv.tow_rntc,
            'placa_veiculo': (inv.tow_plate or '').upper(),
        })]

        res['volume_ids'] = [(0, None, {
            'peso_bruto': inv.weight,
            'peso_liquido': inv.weight_net,
            'quantidade_volumes': inv.number_of_packages,
            'especie': inv.kind_of_packages,
            'marca': inv.brand_of_packages,
            'numeracao': inv.notation_of_packages,
        })]

        res['uf_saida_pais_id'] = inv.uf_saida_pais_id.id
        res['local_embarque'] = inv.local_embarque
        res['local_despacho'] = inv.local_despacho

        return res

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self). \
            _prepare_edoc_item_vals(invoice_line)
        vals['frete'] = invoice_line.valor_frete
        vals['seguro'] = invoice_line.valor_seguro
        vals['outras_despesas'] = invoice_line.outras_despesas
        return vals
