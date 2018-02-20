# © 2009 Gabriel C. Stabel
# © 2009 Renato Lima (Akretion)
# © 2012 Raphaël Valyi (Akretion)
# © 2015  Michell Stuttgart (KMEE)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
import logging
import re

from odoo import _, api, fields, models
from odoo.addons.br_base.tools import fiscal
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import consulta_cadastro
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cnpj_cpf = fields.Char('CNPJ/CPF', size=18, copy=False)
    inscr_est = fields.Char('Inscr. Estadual', size=16, copy=False)
    rg_fisica = fields.Char('RG', size=16, copy=False)
    inscr_mun = fields.Char('Inscr. Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    legal_name = fields.Char(string='Razão Social',
                             size=60,
                             help="Nome utilizado em documentos fiscais")
    city_id = fields.Many2one('res.state.city',
                              'Município',
                              domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char('Número', size=10)

    _sql_constraints = [
        ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)',
         'Já existe um parceiro cadastrado com este CPF/CNPJ!')
    ]

    @api.v8
    def _display_address(self, without_company=False):
        address = self

        if address.country_id and address.country_id.code != 'BR':
            # this ensure other localizations could do what they want
            return super(ResPartner, self)._display_address(
                without_company=False)
        else:
            address_format = (
                address.country_id and address.country_id.address_format or
                "%(street)s\n%(street2)s\n%(city)s %(state_code)s"
                "%(zip)s\n%(country_name)s")
            args = {
                'state_code': address.state_id and address.state_id.code or '',
                'state_name': address.state_id and address.state_id.name or '',
                'country_code': address.country_id and address.country_id.code or '',  # noqa 501
                'country_name': address.country_id and address.country_id.name or '',  # noqa 501
                'company_name': address.parent_id and address.parent_id.name or '',  # noqa 501
                'city_name': address.city_id and address.city_id.name or '',
            }
            address_field = [
                'title',
                'street',
                'street2',
                'zip',
                'city',
                'number',
                'district',
            ]
            for field in address_field:
                args[field] = getattr(address, field) or ''

            if without_company:
                args['company_name'] = ''

            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format

            return address_format % args

    @api.multi
    @api.constrains('cnpj_cpf', 'country_id', 'is_company')
    def _check_cnpj_cpf(self):
        for partner in self:
            country_code = partner.country_id.code or ''
            if partner.cnpj_cpf and country_code.upper() == 'BR':
                if partner.is_company:
                    if not fiscal.validate_cnpj(partner.cnpj_cpf):
                        raise UserError(_('CNPJ inválido!'))
                elif not fiscal.validate_cpf(self.cnpj_cpf):
                    raise UserError(_('CPF inválido!'))
        return True

    @api.multi
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False."""
        self.ensure_one()

        for partner in self:
            if not partner.inscr_est or partner.inscr_est == 'ISENTO' \
                    or not partner.is_company:
                return True
            uf = partner.state_id and partner.state_id.code.lower() or ''
            res = fiscal.validate_ie(uf, partner.inscr_est)
            if not res:
                raise UserError(_('Inscrição Estadual inválida!'))
        return True

    @api.multi
    @api.constrains('inscr_est')
    def _check_ie_duplicated(self):
        """ Check if the field inscr_est has duplicated value
        """
        self.ensure_one()

        for partner in self:
            if not partner.inscr_est or partner.inscr_est == 'ISENTO':
                return True

            partner_ids = self.search([('inscr_est', '=', partner.inscr_est),
                                       ('id', '!=', partner.id)])

            if len(partner_ids) > 0:
                raise UserError(_('Já existe um parceiro cadastrado com'
                                  'esta Inscrição Estadual/RG!'))
        return True

    @api.onchange('cnpj_cpf')
    def onchange_cnpj_cpf(self):

        for partner in self:
            country_code = partner.country_id.code or ''

            if partner.cnpj_cpf and country_code.upper() == 'BR':
                val = re.sub('[^0-9]', '', partner.cnpj_cpf)

                if len(val) == 14:
                    partner.cnpj_cpf = "%s.%s.%s/%s-%s" % (val[0:2],
                                                           val[2:5],
                                                           val[5:8],
                                                           val[8:12],
                                                           val[12:14])

                elif not partner.is_company and len(val) == 11:
                    partner.cnpj_cpf = "%s.%s.%s-%s" % (val[0:3],
                                                        val[3:6],
                                                        val[6:9],
                                                        val[9:11])

                else:
                    raise UserError(_('Verifique o CNPJ/CPF'))

    @api.onchange('city_id')
    def onchange_city_id(self):
        """ Ao alterar o campo city_id copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        for partner in self:
            if partner.city_id:
                partner.city = partner.city_id.name

    @api.onchange('zip')
    def onchange_mask_zip(self):
        for partner in self:
            if partner.zip:
                val = re.sub('[^0-9]', '', partner.zip)
                if len(val) == 8:
                    partner.zip = "%s-%s" % (val[0:5], val[5:8])

    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set.
        Extensão para os novos campos do endereço """
        address_fields = super(ResPartner, self)._address_fields()
        return list(address_fields + ['city_id', 'number', 'district'])

    @api.multi
    def action_check_sefaz(self):

        for partner in self:
            if partner.cnpj_cpf and partner.state_id:

                if partner.state_id.code == 'AL':
                    raise UserError('Alagoas não possui consulta de cadastro')

                if partner.state_id.code == 'RJ':
                    raise UserError(
                        'Rio de Janeiro não possui consulta de cadastro')

                company = self.env.user.company_id

                if not company.nfe_a1_file and not company.nfe_a1_password:
                    raise UserError('Configurar o certificado e senha na '
                                    'empresa')

                cert = company.with_context({'bin_size': False}).nfe_a1_file
                cert_pfx = base64.decodestring(cert)
                certificado = Certificado(cert_pfx, company.nfe_a1_password)
                cnpj = re.sub(r'[^0-9]', '', partner.cnpj_cpf)
                obj = {'cnpj': cnpj, 'estado': partner.state_id.code}
                resposta = consulta_cadastro(certificado, obj=obj, ambiente=1,
                                             estado=partner.state_id.ibge_code)

                obj = resposta['object']

                if "Body" in dir(obj) and "consultaCadastro2Result" in dir(obj.Body):  # noqa: 501
                    info = obj.Body.consultaCadastro2Result.retConsCad.infCons
                    if info.cStat == 111 or info.cStat == 112:
                        if not partner.inscr_est:
                            partner.inscr_est = info.infCad.IE
                        if not partner.cnpj_cpf:
                            partner.cnpj_cpf = info.infCad.IE

                        def get_value(obj, prop):
                            if prop not in dir(obj):
                                return None
                            return getattr(obj, prop)

                        partner.legal_name = get_value(info.infCad, 'xNome')
                        if 'ender' not in dir(info.infCad):
                            return

                        cep = get_value(info.infCad.ender, 'CEP') or ''
                        partner.zip = str(cep).zfill(8) if cep else ''
                        partner.street = get_value(info.infCad.ender, 'xLgr')
                        partner.number = get_value(info.infCad.ender, 'nro')
                        partner.street2 = get_value(info.infCad.ender, 'xCpl')
                        partner.district = get_value(info.infCad.ender,
                                                     'xBairro')
                        cMun = get_value(info.infCad.ender, 'cMun')
                        xMun = get_value(info.infCad.ender, 'xMun')
                        city = None

                        if cMun:
                            city = self.env['res.state.city'].search(
                                [('ibge_code', '=', str(cMun)[2:]),
                                 ('state_id', '=', self.state_id.id)])

                        if not city and xMun:
                            city = self.env['res.state.city'].search(
                                [('name', 'ilike', xMun),
                                 ('state_id', '=', self.state_id.id)])

                        if city:
                            partner.city_id = city.id
                    else:
                        msg = "%s - %s" % (info.cStat, info.xMotivo)
                        raise UserError(msg)
                else:
                    raise UserError("Nenhuma resposta - verificou se seu \
                                    certificado é válido?")
            else:
                raise UserError('Preencha o estado e o CNPJ para pesquisar')
